import os
import requests
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash, send_from_directory
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# โหลด .env สำหรับรันในเครื่องตัวเอง
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__) 

# --- 1. จัดการความลับ (Environment Variables) ---
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_smart_assistant_2026_final')
AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# --- 2. Database Config (ชี้ไปที่บ้าน 'users' ตามรูป Atlas ของพี่) ---
# สำคัญ: ใน Vercel พี่ต้องตั้ง MY_DB_URL ให้ลงท้ายด้วย /users?
app.config["MONGO_URI"] = os.environ.get('MY_DB_URL')
mongo = PyMongo(app)

# ตัวแปรควบคุมสถานะบันทึกแชท (Global Toggle)
SAVE_CHAT_ENABLED = False

# --- 3. Middleware (สิทธิ์การเข้าถึง) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # รองรับทั้ง Admin และ Super Admin ตามที่พี่ต้องการ
        allowed = ['Admin', 'Super Admin']
        if session.get('permission') not in allowed:
            flash('เฉพาะผู้ดูแลระบบเท่านั้น!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 4. Route สำหรับ Favicon (นอก src ตามโครงสร้างไฟล์จริง) ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.abspath(os.path.join(app.root_path, '..')),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- 5. AI API & Chat Control (ดึงข้อมูลนักเรียนจากตาราง students) ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    global SAVE_CHAT_ENABLED
    user_input = request.json.get('message')
    username = session['username']
    permission = session['permission']

    # บันทึกประวัติฝั่ง User ถ้าเปิด Toggle ไว้
    if SAVE_CHAT_ENABLED:
        mongo.db.chat_history.insert_one({
            "username": username, "role": "user", "message": user_input, "timestamp": ObjectId()
        })

    # ดึงข้อมูลนักเรียนตามสิทธิ์ (Admin ดูได้หมด / User ดูตามที่ได้รับอนุญาต)
    if permission in ['Admin', 'Super Admin']:
        students_cursor = mongo.db.students.find()
    else:
        access_list = list(mongo.db.user_access.find({"username": username}))
        gs = [a.get('accessible_grade') for a in access_list if a.get('accessible_grade')]
        sids = [a.get('accessible_student_id') for a in access_list if a.get('accessible_student_id')]
        
        query_parts = []
        if gs: query_parts.append({"grade": {"$in": gs}})
        if sids: query_parts.append({"_id": {"$in": [ObjectId(sid) for sid in sids if sid]}})
        
        students_cursor = mongo.db.students.find({"$or": query_parts}) if query_parts else mongo.db.students.find({"_id": None})

    students = list(students_cursor)
    ctx = "\n".join([f"- {s.get('fullname')} ({s.get('grade')}): {s.get('disability_type','')}" for s in students])

    prompt = f"คุณคือผู้ช่วย ข้อมูลนักเรียน: {ctx}\nคำถาม: {user_input}"
    
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", 
                            headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
                            json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": prompt}]}, 
                            timeout=30)
        reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "AI Error"
        
        if SAVE_CHAT_ENABLED and res.status_code == 200:
            mongo.db.chat_history.insert_one({"username": username, "role": "ai", "message": reply})
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

@app.route('/api/toggle_chat_save', methods=['POST'])
@login_required
@admin_required
def toggle_chat_save():
    global SAVE_CHAT_ENABLED
    SAVE_CHAT_ENABLED = request.json.get('enabled', False)
    return jsonify({"success": True, "enabled": SAVE_CHAT_ENABLED})

@app.route('/api/get_chat_status')
@login_required
def get_chat_status():
    return jsonify({"enabled": SAVE_CHAT_ENABLED})

# --- 6. Auth (Login แบบ No Hash และ Case-Sensitive ตามรูป Atlas: Admin / Ai60kku) ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # ไม่ใช้ .lower() เพื่อให้ตรงกับ "Admin" (A ตัวใหญ่) ในรูป Atlas ของพี่ครับ
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '').strip()
    
    try:
        # ค้นหาใน Database 'users' และ Collection 'users' ตามรูป
        user = mongo.db.users.find_one({"username": u})
        
        if user:
            # เทียบรหัสผ่าน "Ai60kku" ตรงๆ (Plain Text)
            if str(user.get('password')).strip() == p:
                session.update({
                    'username': u, 
                    'displayname': user.get('displayname', u), 
                    'permission': user.get('permission', 'User')
                })
                # ถ้าเป็น Admin หรือ Super Admin ให้ไปที่ Dashboard
                if user.get('permission') in ['Admin', 'Super Admin']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('chatbot_page'))
    except Exception as e:
        print(f"!!! DATABASE ERROR: {str(e)}")

    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

# --- 7. Admin API & Dashboard (จัดการผู้ใช้และสิทธิ์) ---
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = list(mongo.db.users.find())
    all_students = list(mongo.db.students.find().sort("fullname", 1))
    return render_template('admin_dashboard.html', users=users, all_students=all_students)

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
    mongo.db.user_access.insert_one({
        "username": data.get('username'), 
        "accessible_grade": data.get('grade'), 
        "accessible_student_id": data.get('student_id')
    })
    return jsonify({"success": True})

@app.route('/api/revoke_access/<access_id>', methods=['POST'])
@login_required
@admin_required
def revoke_access(access_id):
    mongo.db.user_access.delete_one({"_id": ObjectId(access_id)})
    return jsonify({"success": True})

# --- 8. Navigation & Logout ---
@app.route('/chatbot')
@login_required
def chatbot_page(): return render_template('chatbot.html') 

@app.route('/setting_page')
@login_required
def setting_page(): return render_template('setting.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)