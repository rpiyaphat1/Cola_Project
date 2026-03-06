import os
import requests
import json
import re
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash, send_from_directory
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import pandas as pd 
import io

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__) 

# ✅ Secret Key สำหรับรักษาความปลอดภัยของระบบ Session
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_2026_final_stable_version')

# ---------------------------------------------------------
# 1. DATABASE CONFIGURATION
# ---------------------------------------------------------

# ✅ เชื่อมต่อผ่าน MY_DB_URL (ดึงข้อมูลจาก Database ที่ระบุใน Vercel)
app.config["MONGO_URI"] = os.environ.get('MY_DB_URL')

mongo = PyMongo(app)

# ✅ ค่ากำหนดสำหรับเรียกใช้ AI API
AI_API_KEY = os.environ.get('AI_API_KEY')

AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

SAVE_CHAT_ENABLED = False

# ---------------------------------------------------------
# 2. MIDDLEWARE & ACCESS CONTROL
# ---------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_roles = ['Admin', 'Super Admin']
        if session.get('permission') not in allowed_roles:
            flash('เฉพาะผู้ดูแลระบบเท่านั้นที่มีสิทธิ์เข้าถึง!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------
# 3. STATIC FILES & FAVICON
# ---------------------------------------------------------

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )

# ---------------------------------------------------------
# 4. AUTHENTICATION SYSTEM
# ---------------------------------------------------------

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '') 
    
    try:
        user = mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)})
        
        if user:
            db_pass = user.get('password')
            if db_pass is not None and str(db_pass) == str(p):
                session.update({
                    'username': user.get('username'),
                    'displayname': user.get('displayname', u),
                    'permission': user.get('permission', 'User')
                })
                
                if user.get('permission') in ['Admin', 'Super Admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('student_list_page'))
                
    except Exception as e:
        print(f"❌ Login Error: {str(e)}")
        
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่ครับ', 'error')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_page():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password')
        d = request.form.get('displayname', '').strip()
        perm = request.form.get('permission', 'Teacher')
        
        if mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)}):
            flash('มีชื่อผู้ใช้นี้ในระบบแล้วครับ', 'error')
        else:
            mongo.db.users.insert_one({
                "username": u,
                "password": p,
                "displayname": d,
                "permission": perm
            })
            flash('ลงทะเบียนสำเร็จ!', 'success')
            return redirect(url_for('admin_dashboard'))
            
    return render_template('register.html')

@app.route('/setup_admin')
def setup_admin():
    if not mongo.db.users.find_one({"username": "admin"}):
        mongo.db.users.insert_one({
            "username": "admin",
            "password": "A1234",
            "displayname": "Super Admin",
            "permission": "Super Admin"
        })
        return "สร้างบัญชี Admin เริ่มต้นสำเร็จ! (admin / A1234)"
    return "ระบบมีบัญชี Admin อยู่แล้วใน Database นี้ครับ"

# ---------------------------------------------------------
# 5. ADMIN DASHBOARD (เห็น User ทั้งหมด)
# ---------------------------------------------------------

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        # ✅ ดึงรายชื่อ User ทั้งหมดมาจัดการสิทธิ์
        users = list(mongo.db.users.find())
        all_students = list(mongo.db.students.find().sort("fullname", 1))
        
        all_grades = sorted(list(set([s.get('grade') for s in all_students if s.get('grade')])))
        
        for s in all_students:
            s['id'] = str(s['_id'])
            
        return render_template(
            'admin_dashboard.html', 
            users=users, 
            all_students=all_students, 
            all_grades=all_grades
        )
    except Exception as e:
        return render_template('admin_dashboard.html', error=str(e))

@app.route('/update_user/<username>', methods=['POST'])
@login_required
@admin_required
def update_user(username):
    data = request.json
    if username.lower() == 'admin' or username == session.get('username'):
        perm = mongo.db.users.find_one({"username": username}).get('permission')
    else:
        perm = data.get('permission')
    mongo.db.users.update_one({"username": username}, {"$set": {"displayname": data.get('displayname'), "permission": perm}})
    return jsonify({"success": True})

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    if username.lower() != 'admin' and username != session.get('username'):
        mongo.db.users.delete_one({"username": username})
        mongo.db.user_access.delete_many({"username": username})
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "ไม่สามารถลบผู้ดูแลระบบหลักได้"})

@app.route('/api/get_user_access/<username>')
@login_required
@admin_required
def get_user_access(username):
    accs = list(mongo.db.user_access.find({"username": username}))
    for a in accs:
        a['id'] = str(a['_id'])
    return jsonify({"access": accs})

@app.route('/api/grant_access', methods=['POST'])
@login_required
@admin_required
def grant_access():
    data = request.json
    std_id = data.get('student_id')
    mongo.db.user_access.insert_one({
        "username": data.get('username'), 
        "accessible_grade": data.get('grade'), 
        "accessible_student_id": int(std_id) if std_id else None
    })
    return jsonify({"success": True})

@app.route('/api/revoke_access/<access_id>', methods=['POST'])
@login_required
@admin_required
def revoke_access(access_id):
    mongo.db.user_access.delete_one({"_id": ObjectId(access_id)})
    return jsonify({"success": True})

# ---------------------------------------------------------
# 6. IMPORT SYSTEM & STUDENT DATA
# ---------------------------------------------------------

@app.route('/admin_import')
@login_required
@admin_required
def admin_import_page():
    return render_template('admin_import.html')

@app.route('/api/import_excel', methods=['POST'])
@login_required
@admin_required
def import_excel():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400
        file = request.files['file']
        filename = file.filename.lower()
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8-sig')
        else:
            return jsonify({"success": False, "error": "ใช้ไฟล์ .xlsx หรือ .csv"}), 400
        mapping = {'ชื่อ-นามสกุล': 'fullname', 'ชั้น': 'grade'}
        df = df.rename(columns=mapping)
        df = df.where(pd.notnull(df), None)
        data = df.to_dict(orient='records')
        if data:
            mongo.db.students.insert_many(data)
            return jsonify({"success": True, "message": f"นำเข้าสำเร็จ {len(data)} รายการ"})
        return jsonify({"success": False, "error": "ไฟล์ไม่มีข้อมูล"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/add_student', methods=['POST'])
@login_required
@admin_required
def add_student():
    try:
        data = request.json
        mongo.db.students.insert_one({
            "nickname": data.get('nickname'),
            "fullname": data.get('fullname'),
            "grade": data.get('grade'),
            "disability_type": data.get('disability_type'),
            "technique": data.get('technique'),
            "timestamp": ObjectId()
        })
        return jsonify({"success": True, "message": "บันทึกสำเร็จ!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---------------------------------------------------------
# 7. AI CHAT SYSTEM (GEMINI-2.5-FLASH)
# ---------------------------------------------------------

@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    user_input = request.json.get('message')
    try:
        students = list(mongo.db.students.find().limit(50))
        ctx = "\n".join([f"- {s.get('fullname')} ({s.get('grade')})" for s in students])
        prompt = f"ข้อมูลนักเรียนปัจจุบัน:\n{ctx}\n\nคำถาม: {user_input}"
        res = requests.post(
            f"{AI_BASE_URL}/chat/completions", 
            headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
            json={"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": prompt}]}, 
            timeout=30
        )
        if res.status_code == 200:
            return jsonify({"reply": res.json()['choices'][0]['message']['content']})
        return jsonify({"reply": f"AI ขัดข้อง ({res.status_code})"})
    except Exception as e:
        return jsonify({"reply": f"การเชื่อมต่อผิดพลาด: {str(e)}"}), 500

# ---------------------------------------------------------
# 8. PAGE NAVIGATION (เห็นเฉพาะคนที่มีสิทธิ์)
# ---------------------------------------------------------

@app.route('/chatbot')
@login_required
def chatbot_page():
    return render_template('chatbot.html') 

@app.route('/student_list')
@login_required
def student_list_page():
    username = session.get('username')
    permission = session.get('permission')
    
    # ✅ ถ้าเป็น Admin เห็นทุกคน
    if permission in ['Admin', 'Super Admin']:
        students = list(mongo.db.students.find().sort("fullname", 1))
    else:
        # ✅ ถ้าเป็น Teacher เห็นเฉพาะชั้นเรียนที่มีสิทธิ์
        access = list(mongo.db.user_access.find({"username": username}))
        allowed_grades = [a.get('accessible_grade') for a in access if a.get('accessible_grade')]
        students = list(mongo.db.students.find({"grade": {"$in": allowed_grades}}).sort("fullname", 1))
        
    return render_template('student_list.html', students=students)

@app.route('/setting_page')
@login_required
def setting_page():
    return render_template('setting.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)