import os
import requests
from functools import wraps
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash, send_from_directory
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# โหลด .env สำหรับ Local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__) 

# --- 1. CONFIG & SECRETS ---
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_smart_assistant_2026_final')
AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# เชื่อมต่อ Database IEP ตามมาตรฐานที่พี่ตั้งไว้
app.config["MONGO_URI"] = os.environ.get('MY_DB_URL')
mongo = PyMongo(app)

SAVE_CHAT_ENABLED = False

# --- 2. MIDDLEWARE ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # รองรับสิทธิ์ Admin และ Super Admin ตามโครงสร้างพี่
        allowed = ['Admin', 'Super Admin']
        if session.get('permission') not in allowed:
            flash('เฉพาะผู้ดูแลระบบเท่านั้น!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- 3. FAVICON & STATIC ---
@app.route('/favicon.ico')
def favicon():
    # ดึงจาก static ตามที่พี่แจ้งล่าสุด
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- 4. AUTH & LOGIN (No Hash) ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username', '').strip().lower()
    p = request.form.get('password', '').strip()
    try:
        user = mongo.db.users.find_one({"username": u})
        if user and str(user.get('password')).strip() == p:
            session.update({
                'username': u, 
                'displayname': user.get('displayname', u), 
                'permission': user.get('permission', 'User')
            })
            if user.get('permission') in ['Admin', 'Super Admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('chatbot_page'))
    except Exception as e:
        print(f"!!! DB ERROR: {str(e)}")
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

# --- 5. ADMIN DASHBOARD & USER MANAGEMENT (รองรับ HTML ตัวใหม่ของพี่) ---
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        collections = mongo.db.list_collection_names()
        users = list(mongo.db.users.find())
        all_students = list(mongo.db.students.find().sort("fullname", 1)) if 'students' in collections else []
        
        # ดึงรายชื่อชั้นเรียนสำหรับ Select Box ในหน้า Dashboard
        all_grades = sorted(list(set([s.get('grade') for s in all_students if s.get('grade')])))
        
        # แปลง ID เป็น String ให้ JS เรียกใช้งานได้
        for s in all_students: s['id'] = str(s['_id'])
            
        return render_template('admin_dashboard.html', 
                               users=users, 
                               all_students=all_students, 
                               all_grades=all_grades)
    except Exception as e:
        return render_template('admin_dashboard.html', users=[], all_students=[], all_grades=[], error=str(e))

@app.route('/update_user/<username>', methods=['POST'])
@login_required
@admin_required
def update_user(username):
    data = request.json
    # ล็อคไม่ให้เปลี่ยนสิทธิ์ตัวเองหรือ admin หลัก
    if username == 'admin' or username == session['username']:
        perm = mongo.db.users.find_one({"username": username}).get('permission')
    else:
        perm = data.get('permission')
    
    mongo.db.users.update_one(
        {"username": username},
        {"$set": {"displayname": data.get('displayname'), "permission": perm}}
    )
    return jsonify({"success": True})

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    if username != 'admin' and username != session['username']:
        mongo.db.users.delete_one({"username": username})
        mongo.db.user_access.delete_many({"username": username})
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "ไม่สามารถลบผู้ดูแลระบบได้"})

# --- 6. AI & CHAT CONTROL ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    global SAVE_CHAT_ENABLED
    user_input = request.json.get('message')
    username, permission = session['username'], session['permission']

    if SAVE_CHAT_ENABLED:
        mongo.db.chat_history.insert_one({"username": username, "role": "user", "message": user_input, "timestamp": ObjectId()})

    # ดึงข้อมูลนักเรียนมาช่วยตอบ
    try:
        if permission in ['Admin', 'Super Admin']:
            students = list(mongo.db.students.find())
        else:
            access = list(mongo.db.user_access.find({"username": username}))
            gs = [a.get('accessible_grade') for a in access if a.get('accessible_grade')]
            sids = [a.get('accessible_student_id') for a in access if a.get('accessible_student_id')]
            query = {"$or": [{"grade": {"$in": gs}}, {"_id": {"$in": [ObjectId(sid) for sid in sids if sid]}}]} if gs or sids else {"_id": None}
            students = list(mongo.db.students.find(query))
    except:
        students = []

    ctx = "\n".join([f"- {s.get('fullname')} ({s.get('grade')}): {s.get('disability_type','')}" for s in students])
    prompt = f"คุณคือผู้ช่วย ข้อมูลนักเรียน: {ctx}\nคำถาม: {user_input}"
    
    try:
        res = requests.post(f"{AI_BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {AI_API_KEY}"}, 
                            json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
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

# --- 7. ACCESS CONTROL API ---
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
    # บังคับแปลง student_id เป็น Integer ตามที่ JS ของพี่ส่งมา
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

# --- 8. PAGES ---
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
    app.run(debug=True, host='0.0.0.0', port=8000)