import os
import requests
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# โหลด .env เฉพาะเวลาเทสต์ในเครื่องตัวเอง (Local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- จุดสำคัญ: แก้ไขเพื่อให้หา Templates เจอนอกโฟลเดอร์ src ---
app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

# --- 1. จัดการความลับ (Environment Variables) ---
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# ตัวแปรควบคุมสถานะบันทึกแชท (Global Variable)
SAVE_CHAT_ENABLED = False

# --- 2. Database Config (รองรับ Vercel Postgres) ---
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # แก้ไข Protocol ให้ SQLAlchemy และ pg8000 ทำงานร่วมกันได้
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://") and "+pg8000" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    
    # บังคับใช้ SSL Mode สำหรับฐานข้อมูลบน Cloud
    if "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 3. Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(300), nullable=False)
    displayname = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(20), default='Teacher') # Admin, Teacher, Parent

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False, unique=True)
    grade = db.Column(db.String(20), nullable=False)
    disability_type = db.Column(db.String(50))
    technique = db.Column(db.Text)

class UserAccess(db.Model):
    __tablename__ = 'user_access'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    accessible_grade = db.Column(db.String(20))
    accessible_student_id = db.Column(db.Integer, db.ForeignKey('students.id'))

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    role = db.Column(db.String(20)) # 'user' หรือ 'ai'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# --- 4. Middleware ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('permission') != 'Admin':
            flash('เฉพาะ Admin เท่านั้นที่เข้าหน้านี้ได้!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 5. AI API & Chat Control ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    global SAVE_CHAT_ENABLED
    user_input = request.json.get('message')
    username, permission = session['username'], session['permission']

    if SAVE_CHAT_ENABLED:
        db.session.add(ChatHistory(username=username, role='user', message=user_input))
        db.session.commit()

    if permission == 'Admin':
        students = Student.query.all()
    else:
        access = UserAccess.query.filter_by(username=username).all()
        gs = [a.accessible_grade for a in access if a.accessible_grade]
        sids = [a.accessible_student_id for a in access if a.accessible_student_id]
        students = Student.query.filter((Student.grade.in_(gs)) | (Student.id.in_(sids))).all()

    ctx = "\n".join([f"- {s.fullname} ({s.grade}): {s.disability_type}" for s in students])
    role_th = "คุณครู" if permission == 'Teacher' else "ผู้ปกครอง"
    if permission == 'Admin': role_th = "ผู้ดูแล"

    prompt = f"คุณคือผู้ช่วยของ{role_th} ข้อมูลนักเรียนที่คุณเข้าถึงได้คือ:\n{ctx}\nคำถาม: {user_input}"
    
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
                            json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
        reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "AI Error"
        
        if SAVE_CHAT_ENABLED and res.status_code == 200:
            db.session.add(ChatHistory(username=username, role='ai', message=reply))
            db.session.commit()
            
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

@app.route('/api/toggle_chat_save', methods=['POST'])
@login_required
def toggle_chat_save():
    global SAVE_CHAT_ENABLED
    if session.get('permission') != 'Admin': return jsonify({"success": False}), 403
    SAVE_CHAT_ENABLED = request.json.get('enabled', False)
    return jsonify({"success": True, "enabled": SAVE_CHAT_ENABLED})

@app.route('/api/get_chat_status')
@login_required
def get_chat_status():
    return jsonify({"enabled": SAVE_CHAT_ENABLED})

# --- 6. Auth & User Management ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username', '').lower().strip(), request.form.get('password', '')
    user = User.query.get(u)
    # ใช้ check_password_hash เพื่อความปลอดภัย
    if user and check_password_hash(user.password, p):
        session.update({'username': user.username, 'displayname': user.displayname, 'permission': user.permission})
        return redirect(url_for('admin_dashboard' if user.permission == 'Admin' else 'chatbot_page'))
    flash('ข้อมูลไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    all_students = Student.query.order_by(Student.fullname.asc()).all()
    all_grades = [g[0] for g in db.session.query(Student.grade).distinct().all() if g[0]]
    return render_template('admin_dashboard.html', users=users, all_students=all_students, all_grades=all_grades)

# --- 7. Access Control API ---
@app.route('/api/get_user_access/<username>')
@login_required
@admin_required
def get_user_access(username):
    accs = UserAccess.query.filter_by(username=username).all()
    return jsonify({"access": [{"id": a.id, "grade": a.accessible_grade, "student_id": a.accessible_student_id} for a in accs]})

@app.route('/api/grant_access', methods=['POST'])
@login_required
@admin_required
def grant_access():
    data = request.json
    new_access = UserAccess(
        username=data.get('username'),
        accessible_grade=data.get('grade') if data.get('grade') else None,
        accessible_student_id=int(data.get('student_id')) if data.get('student_id') else None
    )
    db.session.add(new_access)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/revoke_access/<int:access_id>', methods=['POST'])
@login_required
@admin_required
def revoke_access(access_id):
    acc = UserAccess.query.get(access_id)
    if acc:
        db.session.delete(acc); db.session.commit()
    return jsonify({"success": True})

# --- 8. Navigation & Pages ---
@app.route('/chatbot')
@login_required
def chatbot_page(): 
    # ตรวจสอบชื่อไฟล์ให้ตรงกับใน templates (chatbot.html vs Chatbot.html)
    return render_template('chatbot.html') 

@app.route('/student_list_page')
@login_required
def student_list_page():
    u, p = session['username'], session['permission']
    if p == 'Admin':
        stds = Student.query.all()
    else:
        acc = UserAccess.query.filter_by(username=u).all()
        gs = [a.accessible_grade for a in acc if a.accessible_grade]
        sids = [a.accessible_student_id for a in acc if a.accessible_student_id]
        stds = Student.query.filter((Student.grade.in_(gs)) | (Student.id.in_(sids))).all()
    return render_template('student_list.html', students=stds)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

@app.route('/setting_page')
@login_required
def setting_page(): return render_template('setting.html')

# --- 9. Database Initialize ---
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)