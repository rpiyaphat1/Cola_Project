import os
import requests
import io
import pandas as pd
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'iep_smart_assistant_pro_final_fixed'
CORS(app)

# --- 1. Database & AI Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///cola.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

AI_API_KEY = "sk_nTEsUVX3fvu2Hp1WFUW84gq60D4lro2vi0Fd5gwL8hVGBAwyucae3myTk6HsjHBx"
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# --- 2. Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(300), nullable=False)
    displayname = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(20), default='User')

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50))
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

# --- 3. Middleware ---
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
            flash('ขออภัยครับ เฉพาะ Admin เท่านั้นที่เข้าหน้านี้ได้!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 4. AI API Route ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    user_input = request.json.get('message')
    username = session.get('username')
    permission = session.get('permission')

    # 1. ดึงข้อมูลนักเรียนตามสิทธิ์ (Admin เห็นหมด / User เห็นเฉพาะห้อง)
    if permission == 'Admin':
        students = Student.query.all()
    else:
        access = UserAccess.query.filter_by(username=username).all()
        grades = [a.accessible_grade for a in access if a.accessible_grade]
        students = Student.query.filter(Student.grade.in_(grades)).all() if grades else []

    # 2. เตรียม "บริบท" (Context) ให้น้อง AI
    student_context = ""
    for s in students:
        student_context += f"- {s.fullname} (ชั้น {s.grade}): {s.disability_type}, เทคนิค: {s.technique}\n"

    # 3. สร้าง Prompt ที่มีข้อมูลนักเรียนกำกับไว้
    system_prompt = f"คุณคือผู้ช่วยครูการศึกษาพิเศษ ข้อมูลนักเรียนที่คุณมีสิทธิ์เข้าถึงคือ:\n{student_context}\n"
    full_prompt = f"{system_prompt}\nคำถามจากผู้ใช้: {user_input}"

    # 4. ส่งไปหา AI
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gemini-2.5-flash", 
        "messages": [{"role": "user", "content": full_prompt}]
    }
    
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=30)
        data = res.json()
        reply = data['choices'][0]['message']['content'] if 'choices' in data else "AI งงครับ ลองถามใหม่นะ"
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"AI Error: {str(e)}"}), 500

# --- 5. Auth & Navigation ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username', '').lower().strip(), request.form.get('password', '')
    user = User.query.get(u)
    if user and check_password_hash(user.password, p):
        session.update({'username': user.username, 'displayname': user.displayname, 'permission': user.permission})
        return redirect(url_for('chatbot_page' if user.permission == 'Admin' else 'chatbot_page'))
    flash('Username หรือ Password ไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- 6. Admin User Management ---
@app.route('/admin_dashboard')
@login_required
@admin_required 
def admin_dashboard():
    users = User.query.all()
    # ดึงรายชื่อนักเรียนและชั้นเรียนทั้งหมดส่งไปด้วย
    all_students = Student.query.order_by(Student.fullname.asc()).all()
    # ดึงเฉพาะรายชื่อชั้นเรียนแบบไม่ซ้ำ (Unique Grades)
    all_grades = db.session.query(Student.grade).distinct().all()
    all_grades = [g[0] for g in all_grades if g[0]]
    
    return render_template('admin_dashboard.html', 
                           users=users, 
                           all_students=all_students, 
                           all_grades=all_grades)

@app.route('/api/bulk_revoke_access', methods=['POST'])
@login_required
@admin_required
def bulk_revoke_access():
    data = request.json
    access_ids = data.get('access_ids', [])
    if access_ids:
        UserAccess.query.filter(UserAccess.id.in_(access_ids)).delete(synchronize_session=False)
        db.session.commit()
    return jsonify({"success": True})

@app.route('/register_page')
@login_required
@admin_required 
def register_page(): return render_template('register.html')

@app.route('/register', methods=['POST'])
@login_required
@admin_required
def register():
    u, p, d, perm = request.form.get('username', '').lower().strip(), request.form.get('password', ''), request.form.get('displayname', ''), request.form.get('permission', 'User')
    if User.query.get(u):
        flash('Username นี้มีคนใช้แล้วครับ!', 'error')
        return redirect(url_for('register_page'))
    db.session.add(User(username=u, password=generate_password_hash(p), displayname=d, permission=perm))
    db.session.commit()
    flash('สมัครสมาชิกสำเร็จ!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update_user/<username>', methods=['POST'])
@login_required
@admin_required
def update_user(username):
    user = User.query.get(username)
    if user:
        data = request.get_json() 
        user.displayname = data.get('displayname', user.displayname)
        user.permission = data.get('permission', user.permission)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    if username != 'admin':
        user = User.query.get(username)
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({"success": True})
    return jsonify({"success": False}), 403

# --- 7. Student Management & Excel ---
@app.route('/import_page')
@login_required
@admin_required
def import_page(): return render_template('admin_import.html')

@app.route('/api/import_excel', methods=['POST'])
@login_required
@admin_required
def api_import_excel():
    if 'file' not in request.files: return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400
    file = request.files['file']
    try:
        df = pd.read_excel(io.BytesIO(file.read()))
        data = df.to_dict(orient='records')
        count_upd, count_add = 0, 0
        for row in data:
            name = str(row.get('ชื่อ-นามสกุล', '')).strip()
            if not name: continue
            std = Student.query.filter_by(fullname=name).first()
            grade_val = str(row.get('ชั้น', '')).strip()
            
            # รวมข้อมูลอาการและวิธีแก้
            tech_val = f"ปัญหา: {row.get('อาการ/ปัญหา', '-')} | วิธีรับมือ: {row.get('วิธีรับมือ', '-')}"
            
            if std:
                std.nickname = row.get('ชื่อเล่น')
                std.grade = grade_val
                std.disability_type = row.get('วิชาที่บกพร่อง')
                std.technique = tech_val
                count_upd += 1
            else:
                db.session.add(Student(
                    fullname=name, nickname=row.get('ชื่อเล่น'), grade=grade_val,
                    disability_type=row.get('วิชาที่บกพร่อง'), technique=tech_val
                ))
                count_add += 1
        db.session.commit()
        return jsonify({"success": True, "message": f"เพิ่มใหม่ {count_add}, อัปเดต {count_upd} รายการ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/add_student', methods=['POST'])
@login_required
@admin_required
def api_add_student():
    try:
        data = request.get_json()
        if not data.get('fullname') or not data.get('grade'):
            return jsonify({"success": False, "error": "กรุณาระบุชื่อและชั้นเรียน"}), 400
        db.session.add(Student(
            nickname=data.get('nickname'), fullname=data.get('fullname'),
            grade=data.get('grade'), disability_type=data.get('disability_type'),
            technique=data.get('technique')
        ))
        db.session.commit()
        return jsonify({"success": True, "message": "บันทึกสำเร็จ!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# --- 8. Student List & Access Control ---
@app.route('/student_list_page')
@login_required
def student_list_page():
    if session.get('permission') == 'Admin':
        students = Student.query.order_by(Student.grade.asc(), Student.fullname.asc()).all()
    else:
        access = UserAccess.query.filter_by(username=session['username']).all()
        grades = [a.accessible_grade for a in access if a.accessible_grade]
        students = Student.query.filter(Student.grade.in_(grades)).order_by(Student.grade.asc()).all()
    return render_template('student_list.html', students=students)

@app.route('/api/get_user_access/<username>')
@login_required
@admin_required
def get_user_access(username):
    accesses = UserAccess.query.filter_by(username=username).all()
    return jsonify({"access": [{"id": a.id, "grade": a.accessible_grade} for a in accesses]})

@app.route('/api/grant_access', methods=['POST'])
@login_required
@admin_required
def grant_access():
    data = request.json
    db.session.add(UserAccess(username=data['username'], accessible_grade=data['grade']))
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/revoke_access/<int:access_id>', methods=['POST'])
@login_required
@admin_required
def revoke_access(access_id):
    acc = UserAccess.query.get(access_id)
    if acc:
        db.session.delete(acc)
        db.session.commit()
    return jsonify({"success": True})

# --- 9. Extra Pages ---
@app.route('/chatbot')
@login_required
def chatbot_page(): return render_template('Chatbot.html')

@app.route('/setting_page')
@login_required
def setting_page(): return render_template('setting.html')

if __name__ == "__main__":
    with app.app_context(): db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)