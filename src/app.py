import os
import requests
import json
import re  # ✅ สำหรับการค้นหาแบบไม่สนตัวพิมพ์เล็ก-ใหญ่
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash, send_from_directory
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

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
    p = request.form.get('password', '') # ❌ ไม่ต้อง .strip() ที่รหัสผ่านเพื่อให้ได้ค่าจริง
    
    try:
        # ✅ ค้นหา Username แบบ Case-insensitive
        user = mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)})
        
        if user:
            # ✅ ดึงค่า Password จาก DB มาตรวจสอบก่อนว่าเป็น None ไหม
            raw_db_pass = user.get('password')
            
            if raw_db_pass is not None:
                # ✅ แปลงเป็น String แค่ตัวข้อมูลข้างในจริงๆ
                db_pass = str(raw_db_pass)
                
                # ✅ เทียบรหัสผ่านแบบตรงตัว (Case-sensitive สำหรับรหัสผ่าน)
                if db_pass == p:
                    session.update({
                        'username': user.get('username'),
                        'displayname': user.get('displayname', u),
                        'permission': user.get('permission', 'User')
                    })
                    
                    if user.get('permission') in ['Admin', 'Super Admin']:
                        return redirect(url_for('admin_dashboard'))
                    return redirect(url_for('chatbot_page'))
                    
    except Exception as e:
        print(f"Login Error: {str(e)}")
        
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_page():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '').strip()
        d = request.form.get('displayname', '').strip()
        perm = request.form.get('permission', 'Teacher')
        
        if mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)}):
            flash('มีชื่อผู้ใช้นี้ในระบบแล้ว', 'error')
        else:
            mongo.db.users.insert_one({
                "username": u,
                "password": p, # บันทึกแบบธรรมดา
                "displayname": d,
                "permission": perm
            })
            flash('ลงทะเบียนสำเร็จ!', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

# --- 5. ADMIN TOOLS (Dashboard & Import) ---
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

@app.route('/api/import_students', methods=['POST'])
@login_required
@admin_required
def import_students():
    try:
        data = request.json
        if not data or not isinstance(data, list):
            return jsonify({"success": False, "message": "Invalid format"}), 400
        mongo.db.students.insert_many(data)
        return jsonify({"success": True, "count": len(data)})
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
    global SAVE_CHAT_ENABLED
    user_input = request.json.get('message')
    username, permission = session['username'], session['permission']
    
    if SAVE_CHAT_ENABLED:
        mongo.db.chat_history.insert_one({"username": username, "role": "user", "message": user_input, "timestamp": ObjectId()})

    try:
        if permission in ['Admin', 'Super Admin']:
            students = list(mongo.db.students.find())
        else:
            access = list(mongo.db.user_access.find({"username": username}))
            gs = [a.get('accessible_grade') for a in access if a.get('accessible_grade')]
            sids = [a.get('accessible_student_id') for a in access if a.get('accessible_student_id')]
            # กรองข้อมูลนักเรียนตามสิทธิ์ที่ได้รับ
            query = {"$or": [{"grade": {"$in": gs}}, {"_id": {"$in": [ObjectId(sid) for sid in sids if sid]}}]} if gs or sids else {"_id": None}
            students = list(mongo.db.students.find(query))
    except: students = []

    ctx = "\n".join([f"- {s.get('fullname')} ({s.get('grade')}): {s.get('disability_type','')}" for s in students])
    prompt = f"คุณคือผู้ช่วย ข้อมูลนักเรียน: {ctx}\nคำถาม: {user_input}"
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
                            json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
        reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "AI Error"
        if SAVE_CHAT_ENABLED and res.status_code == 200:
            mongo.db.chat_history.insert_one({"username": username, "role": "ai", "message": reply})
        return jsonify({"reply": reply})
    except Exception as e: return jsonify({"reply": f"Error: {str(e)}"}), 500

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