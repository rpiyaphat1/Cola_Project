import os
import requests
import json
import re  # ✅ สำหรับการค้นหาแบบไม่สนตัวพิมพ์เล็ก-ใหญ่
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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_2026_final_stable_version')

# --- 1. Database Config ---
app.config["MONGO_URI"] = os.environ.get('MY_DB_URL')
mongo = PyMongo(app)

AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"
SAVE_CHAT_ENABLED = False

# --- 2. Middleware (ตรวจสอบสิทธิ์) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ✅ รองรับทั้ง Admin และ Super Admin
        allowed_roles = ['Admin', 'Super Admin']
        if session.get('permission') not in allowed_roles:
            flash('เฉพาะผู้ดูแลระบบเท่านั้น!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 3. Favicon ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- 4. AUTH SYSTEM (Login & Register - แบบรหัสผ่านตรงตัว) ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '') # รับค่ารหัสผ่านดิบๆ
    
    try:
        user = mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)})
        
        if user:
            db_pass = user.get('password')
            
            print(f"--- DEBUG LOGIN ---")
            print(f"What you typed: '{p}'")
            print(f"What's in DB:   '{db_pass}'")
            print(f"Are they equal?: {str(db_pass) == str(p)}")
            print(f"-------------------")

            if db_pass is not None and str(db_pass) == str(p):
                session.update({
                    'username': user.get('username'),
                    'displayname': user.get('displayname', u),
                    'permission': user.get('permission', 'User') # รองรับสิทธิ์ Super Admin
                })
                dest = 'admin_dashboard' if user.get('permission') in ['Admin', 'Super Admin'] else 'chatbot_page'
                return redirect(url_for(dest))
                
    except Exception as e:
        print(f"❌ Login Error: {str(e)}")
        
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
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
            flash('มีชื่อผู้ใช้นี้ในระบบแล้ว', 'error')
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

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        users = list(mongo.db.users.find())
        all_students = list(mongo.db.students.find().sort("fullname", 1))
        all_grades = sorted(list(set([s.get('grade') for s in all_students if s.get('grade')])))
        for s in all_students: s['id'] = str(s['_id'])
        return render_template('admin_dashboard.html', users=users, all_students=all_students, all_grades=all_grades)
    except Exception as e:
        return render_template('admin_dashboard.html', users=[], all_students=[], all_grades=[], error=str(e))

@app.route('/admin_import')
@login_required
@admin_required
def admin_import_page():
    return render_template('admin_import.html')

# --- 2. API สำหรับอัปโหลดไฟล์ Excel/CSV (จากปุ่ม startUpload) ---
@app.route('/api/import_excel', methods=['POST'])
@login_required
@admin_required
def import_excel():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "ไม่พบไฟล์ที่ส่งมาครับพี่"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "พี่ไม่ได้เลือกไฟล์ครับ"}), 400

        filename = file.filename.lower()
        
        # อ่านไฟล์ตามประเภท
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({"success": False, "error": "รองรับเฉพาะ .xlsx และ .csv เท่านั้นครับ"}), 400

        # ล้างค่าว่างให้ MongoDB อ่านออก
        df = df.where(pd.notnull(df), None)
        data = df.to_dict(orient='records')

        if data:
            # ✨ บันทึกลง Collection 'students' ทันที
            mongo.db.students.insert_many(data)
            return jsonify({"success": True, "message": f"นำเข้าข้อมูลสำเร็จ {len(data)} รายการแล้วครับ!"})
        
        return jsonify({"success": False, "error": "ไฟล์นี้ไม่มีข้อมูลเลยพี่"}), 400

    except Exception as e:
        print(f"Excel Import Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- 3. API สำหรับบันทึกรายคน (จากปุ่ม saveStudent) ---
@app.route('/api/add_student', methods=['POST'])
@login_required
@admin_required
def add_student():
    try:
        data = request.json
        if not data.get('fullname') or not data.get('grade'):
            return jsonify({"success": False, "message": "กรุณาระบุชื่อและชั้นเรียนด้วยครับ"}), 400
            
        # บันทึกลง MongoDB
        mongo.db.students.insert_one({
            "nickname": data.get('nickname'),
            "fullname": data.get('fullname'),
            "grade": data.get('grade'),
            "disability_type": data.get('disability_type'),
            "technique": data.get('technique'),
            "timestamp": ObjectId() # เก็บเวลาสร้างไว้หน่อย
        })
        return jsonify({"success": True, "message": "บันทึกข้อมูลนักเรียนสำเร็จครับ!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- 6. USER & ACCESS MANAGEMENT (ฟังก์ชันจัดการผู้ใช้ - ห้ามลบ) ---
@app.route('/update_user/<username>', methods=['POST'])
@login_required
@admin_required
def update_user(username):
    data = request.json
    # ห้ามเปลี่ยนสิทธิ์ตัวเองหรือ admin หลัก
    if username.lower() == 'admin' or username == session.get('username'):
        perm = mongo.db.users.find_one({"username": username}).get('permission')
    else: perm = data.get('permission')
    mongo.db.users.update_one({"username": username}, {"$set": {"displayname": data.get('displayname'), "permission": perm}})
    return jsonify({"success": True})

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    # ป้องกันการลบตัวเองหรือ admin หลัก
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
    for a in accs: a['id'] = str(a['_id'])
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

# --- 7. AI CHAT ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    user_input = request.json.get('message')
    username = session.get('username')
    permission = session.get('permission')
    
    # 1. ลองดึงข้อมูลนักเรียน (ถ้ามี)
    try:
        students = list(mongo.db.students.find().limit(20))
    except:
        students = []

    # 2. สร้าง Context (ถ้าไม่มีนักเรียน ก็ให้เป็นค่าว่างไป)
    if students:
        ctx = "\n".join([f"- {s.get('fullname')} ({s.get('grade')})" for s in students])
        prompt = f"ข้อมูลนักเรียนที่มีในระบบ:\n{ctx}\n\nคำถามจากผู้ใช้: {user_input}"
    else:
        # 💡 ถ้าไม่มีข้อมูลนักเรียน ให้ AI ตอบแบบทั่วไปเพื่อทดสอบการเชื่อมต่อ
        prompt = f"ระบบกำลังอยู่ในโหมดทดสอบ (ยังไม่มีข้อมูลนักเรียนใน DB)\nคำถามคือ: {user_input}"

    try:
        # 3. ยิงไปหา AI API (ใช้ Key จาก Vercel Settings)
        res = requests.post(
            f"{AI_BASE_URL}/chat/completions", 
            headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
            json={
                "model": "gemini-2.0-flash", 
                "messages": [{"role": "user", "content": prompt}]
            }, 
            timeout=30
        )
        
        if res.status_code == 200:
            reply = res.json()['choices'][0]['message']['content']
        else:
            reply = f"AI ตอบกลับไม่ได้ (Error: {res.status_code})"
            print(f"AI API Log: {res.text}") # ดูใน Vercel Runtime Logs

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"การเชื่อมต่อผิดพลาด: {str(e)}"}), 500

# --- 8. PAGE NAVIGATION ---
@app.route('/chatbot')
@login_required
def chatbot_page(): return render_template('chatbot.html') 

@app.route('/setting_page')
@login_required
def setting_page(): return render_template('setting.html')

@app.route('/student_list')
@login_required
def student_list_page(): return render_template('student_list.html')

if __name__ == "__main__":
    # รันบนเครื่องตัวเองที่ Port 8000
    app.run(debug=True, host='0.0.0.0', port=8000)