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
CORS(app) # อนุญาตให้เรียกใช้ API ข้าม Service ได้

# --- 1. Database & AI Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://piyaphatrattanarak@localhost/cola_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

AI_API_KEY = "sk_nTEsUVX3fvu2Hp1WFUW84gq60D4lro2vi0Fd5gwL8hVGBAwyucae3myTk6HsjHBx"
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1/chat/completions"

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(300), nullable=False)
    displayname = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(20), default='User')

# --- 2. Middleware (ระบบคุมสิทธิ์) ---
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
            flash('ขออภัยครับพี่ เฉพาะ Admin เท่านั้นที่เข้าหน้านี้ได้!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 3. AI API (Gemini 2.0 Pro) ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    user_input = request.json.get('message')
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gemini-2.0-pro",
        "messages": [{"role": "user", "content": user_input}]
    }
    try:
        res = requests.post(AI_BASE_URL, headers=headers, json=payload, timeout=30)
        return jsonify({"reply": res.json()['choices'][0]['message']['content']})
    except:
        return jsonify({"reply": "AI กำลังประมวลผลอยู่ครับพี่ ลองใหม่อีกทีนะ"}), 500

# --- 4. Routes (Authentication & Navigation) ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username', '').lower().strip(), request.form.get('password', '')
    user = User.query.get(u)
    if user and check_password_hash(user.password, p):
        session.update({
            'username': user.username, 
            'displayname': user.displayname, 
            'permission': user.permission
        })
        if user.permission == 'Admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('chatbot_page'))
            
    flash('Username หรือ Password ไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

# --- 5. Admin Routes ---
@app.route('/admin_dashboard')
@login_required
@admin_required 
def admin_dashboard(): 
    return render_template('admin_dashboard.html', users=User.query.all())

@app.route('/register_page')
@login_required
@admin_required 
def register_page(): 
    return render_template('register.html')

@app.route('/register', methods=['POST'])
@login_required
@admin_required
def register():
    u = request.form.get('username', '').lower().strip()
    p = request.form.get('password', '')
    d = request.form.get('displayname', '')
    perm = request.form.get('permission', 'User')

    if User.query.get(u):
        flash('Username นี้มีคนใช้แล้วครับพี่!', 'error')
        return redirect(url_for('register_page'))

    new_user = User(username=u, password=generate_password_hash(p), 
                    displayname=d, permission=perm)
    db.session.add(new_user)
    db.session.commit()
    
    flash('สมัครสมาชิกสำเร็จแล้ว!', 'success')
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

# --- 6. ส่วนที่เพิ่มใหม่: Import Data Service (ห้ามลบ) ---
@app.route('/import_page')
@login_required
@admin_required
def import_page():
    return render_template('admin_import.html')

@app.route('/api/import_excel', methods=['POST'])
@login_required
@admin_required
def api_import_excel():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "ไม่ได้เลือกไฟล์"}), 400

    try:
        # ใช้ Pandas อ่านไฟล์จาก Buffer
        df = pd.read_excel(io.BytesIO(file.read()))
        data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True, 
            "message": f"Flask API ประมวลผลสำเร็จ {len(data)} รายการ",
            "data": data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- 7. User Routes ---
@app.route('/chatbot')
@login_required
def chatbot_page(): 
    return render_template('Chatbot.html')

@app.route('/student_list_page')
@login_required
def student_list_page(): 
    return render_template('student_list.html')

@app.route('/setting_page')
@login_required
def setting_page(): 
    return render_template('setting.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    with app.app_context(): db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)