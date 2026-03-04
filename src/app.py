import os
import requests
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

# โหลด .env เฉพาะเวลาเทสต์ในเครื่องตัวเอง (Local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__) 

# --- 1. จัดการความลับ (Environment Variables) ---
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_secret_key_2026')
AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# --- 2. Database Config ---
raw_uri = os.environ.get('MONGODB_URI')

if raw_uri:
    # บังคับให้วิ่งไปหา Database ชื่อ 'user' (ตามรูป image_45f263.jpg)
    if "user?" not in raw_uri:
        if "?" in raw_uri:
            final_uri = raw_uri.replace("?", "user?")
        else:
            final_uri = raw_uri.rstrip('/') + "/user"
    else:
        final_uri = raw_uri
else:
    final_uri = None

app.config["MONGO_URI"] = final_uri
mongo = PyMongo(app)

SAVE_CHAT_ENABLED = False

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
            flash('เฉพาะ Admin เท่านั้นที่เข้าหน้านี้ได้!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 4. AI API & Chat Control ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    global SAVE_CHAT_ENABLED
    user_input = request.json.get('message')
    username, permission = session['username'], session['permission']

    if SAVE_CHAT_ENABLED:
        mongo.db.chat_history.insert_one({
            "username": username,
            "role": "user",
            "message": user_input,
            "timestamp": ObjectId()
        })

    if permission == 'Admin':
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
    role_th = "คุณครู" if permission == 'Teacher' else "ผู้ปกครอง"
    if permission == 'Admin': role_th = "ผู้ดูแล"

    prompt = f"คุณคือผู้ช่วยของ{role_th} ข้อมูลนักเรียนที่คุณเข้าถึงได้คือ:\n{ctx}\nคำถาม: {user_input}"
    
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
                            json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
        reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "AI Error"
        
        if SAVE_CHAT_ENABLED and res.status_code == 200:
            mongo.db.chat_history.insert_one({"username": username, "role": "ai", "message": reply})
            
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

# --- 5. Auth & User Management ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # .strip() สำคัญมาก กันพี่เผลอเคาะ space ตอนพิมพ์
    u = request.form.get('username', '').lower().strip()
    p = request.form.get('password', '').strip()
    
    # ดึงจาก Collection 'users' (มี s) ตามที่พี่แจ้งล่าสุด
    user = mongo.db.users.find_one({"username": u})
    
    if user:
        # เปรียบเทียบรหัสผ่านที่รับมา กับ Hash ใน Database
        if check_password_hash(user['password'], p):
            session.update({
                'username': user['username'], 
                'displayname': user['displayname'], 
                'permission': user['permission']
            })
            if user['permission'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('chatbot_page'))
    
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = list(mongo.db.users.find())
    all_students = list(mongo.db.students.find().sort("fullname", 1))
    all_grades = mongo.db.students.distinct("grade")
    return render_template('admin_dashboard.html', users=users, all_students=all_students, all_grades=all_grades)

# --- 6. Access Control API ---
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
        "accessible_grade": data.get('grade') if data.get('grade') else None,
        "accessible_student_id": data.get('student_id') if data.get('student_id') else None
    })
    return jsonify({"success": True})

@app.route('/api/revoke_access/<access_id>', methods=['POST'])
@login_required
@admin_required
def revoke_access(access_id):
    mongo.db.user_access.delete_one({"_id": ObjectId(access_id)})
    return jsonify({"success": True})

# --- 7. Navigation & Pages ---
@app.route('/chatbot')
@login_required
def chatbot_page(): return render_template('chatbot.html') 

@app.route('/student_list_page')
@login_required
def student_list_page():
    u, p = session['username'], session['permission']
    if p == 'Admin':
        stds = list(mongo.db.students.find())
    else:
        access = list(mongo.db.user_access.find({"username": u}))
        gs = [a.get('accessible_grade') for a in access if a.get('accessible_grade')]
        sids = [a.get('accessible_student_id') for a in access if a.get('accessible_student_id')]
        
        query_parts = []
        if gs: query_parts.append({"grade": {"$in": gs}})
        if sids: query_parts.append({"_id": {"$in": [ObjectId(sid) for sid in sids if sid]}})
        
        stds = list(mongo.db.students.find({"$or": query_parts})) if query_parts else []
    return render_template('student_list.html', students=stds)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

@app.route('/setting_page')
@login_required
def setting_page(): return render_template('setting.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)