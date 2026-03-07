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

# พยายามโหลดค่าจากไฟล์ .env สำหรับการทดสอบในเครื่อง
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__) 

# ✅ Secret Key สำหรับรักษาความปลอดภัยของระบบ Session ป้องกันการปลอมแปลงคุกกี้
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'piyaphat_2026_final_stable_version')

# -----------------------------------------------------------------------------
# 1. DATABASE CONFIGURATION (การตั้งค่าฐานข้อมูล)
# -----------------------------------------------------------------------------

# ✅ ดึงค่า MONGO_URI จากตัวแปร MY_DB_URL ใน Vercel
# ⚠️ ตรวจสอบให้มั่นใจว่าใน Vercel ระบุชื่อ Database ต่อท้าย (เช่น /IEP หรือ /users)
app.config["MONGO_URI"] = os.environ.get('MY_DB_URL')

# เริ่มต้นการเชื่อมต่อกับ MongoDB
mongo = PyMongo(app)

# ✅ ค่ากำหนดสำหรับเรียกใช้ AI API ของมหาวิทยาลัยขอนแก่น
AI_API_KEY = os.environ.get('AI_API_KEY')
AI_BASE_URL = "https://gen.ai.kku.ac.th/api/v1"

# กำหนดสถานะการบันทึกประวัติแชท
SAVE_CHAT_ENABLED = False

# -----------------------------------------------------------------------------
# 2. MIDDLEWARE & ACCESS CONTROL (ระบบรักษาความปลอดภัย)
# -----------------------------------------------------------------------------

def login_required(f):
    """ Middleware สำหรับตรวจสอบว่าผู้ใช้ล็อกอินหรือยังก่อนเข้าถึงหน้าต่างๆ """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """ Middleware สำหรับตรวจสอบสิทธิ์เฉพาะ Admin หรือ Super Admin เท่านั้น """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_roles = ['Admin', 'Super Admin']
        if session.get('permission') not in allowed_roles:
            flash('เฉพาะผู้ดูแลระบบเท่านั้นที่มีสิทธิ์เข้าถึงส่วนนี้!', 'error')
            return redirect(url_for('chatbot_page'))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------------------------------------------------------
# 3. STATIC FILES (ไฟล์คงที่และ Favicon)
# -----------------------------------------------------------------------------

@app.route('/favicon.ico')
def favicon():
    """ ส่งไฟล์ไอคอนของเว็บไซต์ """
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )

# -----------------------------------------------------------------------------
# 4. AUTHENTICATION SYSTEM (ระบบจัดการผู้ใช้และล็อกอิน)
# -----------------------------------------------------------------------------

@app.route('/')
def login_page():
    """ หน้าแรกสำหรับล็อกอินเข้าสู่ระบบ """
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """ จัดการการตรวจสอบชื่อผู้ใช้และรหัสผ่าน """
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '') 
    
    try:
        # ค้นหาผู้ใช้โดยไม่สนใจตัวพิมพ์เล็กหรือใหญ่ (Case-insensitive)
        user = mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)})
        
        if user:
            db_pass = user.get('password')
            # ตรวจสอบรหัสผ่านที่เก็บใน Database (แบบ Plain Text ตามโครงสร้างเดิม)
            if db_pass is not None and str(db_pass) == str(p):
                session.update({
                    'username': user.get('username'),
                    'displayname': user.get('displayname', u),
                    'permission': user.get('permission', 'User')
                })
                
                # แยกหน้าแรกตามสิทธิ์ของผู้ใช้งาน
                if user.get('permission') in ['Admin', 'Super Admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('student_list_page'))
                
    except Exception as e:
        print(f"❌ Login Database Error: {str(e)}")
        
    flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่ครับ', 'error')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    """ ล้างข้อมูล Session และออกจากระบบ """
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_page():
    """ หน้าสำหรับ Admin ในการลงทะเบียนผู้ใช้งานใหม่ """
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password')
        d = request.form.get('displayname', '').strip()
        perm = request.form.get('permission', 'Teacher')
        
        # ตรวจสอบว่ามีชื่อผู้ใช้นี้อยู่แล้วหรือไม่
        if mongo.db.users.find_one({"username": re.compile(f'^{u}$', re.IGNORECASE)}):
            flash('ขออภัย มีชื่อผู้ใช้นี้ในระบบแล้วครับ', 'error')
        else:
            mongo.db.users.insert_one({
                "username": u,
                "password": p,
                "displayname": d,
                "permission": perm
            })
            flash('ลงทะเบียนผู้ใช้ใหม่สำเร็จ!', 'success')
            return redirect(url_for('admin_dashboard'))
            
    return render_template('register.html')

# -----------------------------------------------------------------------------
# 5. ADMIN DASHBOARD & USER MANAGEMENT (จุดที่แก้ไขคืนค่า Card User)
# -----------------------------------------------------------------------------

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    """ หน้าแดชบอร์ดสำหรับจัดการผู้ใช้: คืนค่าการดึง Users ทั้งหมดเพื่อโชว์ใน Frontend """
    try:
        # ✅ 1. ดึงรายชื่อผู้ใช้ทั้งหมดจากตาราง users มาแสดงผล (คืนค่า Card User)
        users = list(mongo.db.users.find())
        
        # ✅ 2. ดึงรายชื่อนักเรียนทั้งหมดและเรียงตามชื่อ (เพื่อใช้ในระบบ Search รายคน)
        all_students = list(mongo.db.students.find().sort("fullname", 1))
        
        # ✅ 3. กรองรายชื่อระดับชั้นที่ไม่ซ้ำกัน (เพื่อใช้ในระบบ Search รายห้อง)
        all_grades = sorted(list(set([s.get('grade') for s in all_students if s.get('grade')])))
        
        # ✅ 4. เตรียมข้อมูล ObjectId ให้เป็น String เพื่อให้ JavaScript ฝั่ง Frontend อ่านได้
        for s in all_students:
            s['id'] = str(s['_id'])
            
        # ✅ 5. ส่งข้อมูลทั้งหมดไปยัง Template admin_dashboard.html
        return render_template(
            'admin_dashboard.html', 
            users=users, 
            all_students=all_students, 
            all_grades=all_grades
        )
    except Exception as e:
        print(f"❌ Dashboard Error: {str(e)}")
        # หากเกิด Error ให้ส่งตัวแปรว่างไปป้องกันหน้าขาวพัง
        return render_template('admin_dashboard.html', users=[], all_students=[], all_grades=[], error=str(e))

@app.route('/update_user/<username>', methods=['POST'])
@login_required
@admin_required
def update_user(username):
    """ อัปเดตข้อมูลโปรไฟล์และสิทธิ์ของผู้ใช้งาน """
    data = request.json
    
    # ป้องกันการเปลี่ยนสิทธิ์ตัวเองหรือบัญชี admin หลักเพื่อความปลอดภัย
    if username.lower() == 'admin' or username == session.get('username'):
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
    """ ลบผู้ใช้งานและสิทธิ์การเข้าถึงทั้งหมดของผู้ใช้งานนั้นๆ """
    if username.lower() != 'admin' and username != session.get('username'):
        mongo.db.users.delete_one({"username": username})
        mongo.db.user_access.delete_many({"username": username})
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "ไม่สามารถลบผู้ดูแลระบบหลักได้"})

@app.route('/api/get_user_access/<username>')
@login_required
@admin_required
def get_user_access(username):
    """ ดึงข้อมูลสิทธิ์การเข้าถึงรายห้อง/รายคน ของผู้ใช้งาน """
    accs = list(mongo.db.user_access.find({"username": username}))
    for a in accs:
        a['id'] = str(a['_id'])
    return jsonify({"access": accs})

@app.route('/api/grant_access', methods=['POST'])
@login_required
@admin_required
def grant_access():
    """ มอบสิทธิ์การเข้าถึงชั้นเรียนหรือนักเรียนรายบุคคลให้ผู้ใช้ """
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
    """ ยกเลิกสิทธิ์การเข้าถึงที่เคยระบุไว้ """
    mongo.db.user_access.delete_one({"_id": ObjectId(access_id)})
    return jsonify({"success": True})

# -----------------------------------------------------------------------------
# 6. IMPORT SYSTEM & STUDENT DATA (การนำเข้าและจัดการนักเรียน)
# -----------------------------------------------------------------------------

@app.route('/admin_import')
@login_required
@admin_required
def admin_import_page():
    """ หน้าสำหรับเลือกไฟล์ Excel/CSV เพื่อนำเข้าข้อมูล """
    return render_template('admin_import.html')

@app.route('/api/import_excel', methods=['POST'])
@login_required
@admin_required
def import_excel():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "ไม่พบไฟล์ที่ส่งมาครับ"}), 400
        
        file = request.files['file']
        filename = file.filename.lower()
        
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8-sig')
        else:
            return jsonify({"success": False, "error": "รองรับเฉพาะไฟล์ .xlsx และ .csv เท่านั้น"}), 400

        # ✅ 1. Mapping หัวคอลัมน์
        mapping = {
            'เลขที่': 'student_id',
            'ชื่อ-นามสกุล': 'fullname',
            'ชื่อเล่น': 'nickname',
            'ชั้น': 'grade',
            'วิชาที่บกพร่อง': 'disability_type',
            'วิชาที่โดดเด่น': 'outstanding_subject',
            'หมายเหตุ': 'note'
        }
        df = df.rename(columns=mapping)

        # ✅ 2. รวมข้อมูลสำหรับ AI (technique)
        df['technique'] = (
            "วิชาที่บกพร่อง: " + df['disability_type'].fillna('-').astype(str) + 
            " | วิชาที่โดดเด่น: " + df['outstanding_subject'].fillna('-').astype(str) + 
            " | หมายเหตุ: " + df['note'].fillna('-').astype(str)
        )

        df = df.where(pd.notnull(df), None)
        data = df.to_dict(orient='records')

        import_count = 0
        skip_count = 0

        if data:
            # ✅ 3. วนลูปเช็คทีละคนก่อน Insert เพื่อป้องกันชื่อซ้ำ
            for student in data:
                # ตรวจสอบจากชื่อ-นามสกุล (fullname)
                # ใช้ strip() เพื่อป้องกันช่องว่างส่วนเกินที่ทำให้มองว่าไม่ซ้ำ
                name_to_check = str(student['fullname']).strip()
                
                exists = mongo.db.students.find_one({"fullname": name_to_check})
                
                if not exists:
                    # ถ้ายังไม่มีในระบบ ให้บันทึก
                    mongo.db.students.insert_one(student)
                    import_count += 1
                else:
                    # ถ้ามีแล้ว ให้ข้าม (หรือพี่จะเปลี่ยนเป็น update_one ก็ได้นะ)
                    skip_count += 1
            
            return jsonify({
                "success": True, 
                "message": f"นำเข้าสำเร็จ {import_count} รายการ (พบชื่อซ้ำข้ามไป {skip_count} รายการ)"
            })
        
        return jsonify({"success": False, "error": "ไม่พบข้อมูลในไฟล์ที่เลือก"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/add_student', methods=['POST'])
@login_required
@admin_required
def add_student():
    try:
        data = request.json
        # ดึงชื่อออกมาแล้วตัดช่องว่างหัว-ท้าย เพื่อความแม่นยำในการเช็คซ้ำ
        fullname = str(data.get('fullname', '')).strip()
        grade = data.get('grade')

        if not fullname or not grade:
            return jsonify({"success": False, "message": "กรุณาระบุชื่อและชั้นเรียนด้วยครับ"}), 400
            
        # ✅ 1. ตรวจสอบว่าชื่อ-นามสกุลนี้ มีอยู่ในฐานข้อมูลแล้วหรือยัง
        exists = mongo.db.students.find_one({"fullname": fullname})
        if exists:
            return jsonify({
                "success": False, 
                "message": f"ขออภัย รายชื่อ '{fullname}' มีอยู่ในระบบแล้ว (ชั้น {exists.get('grade')})"
            }), 400

        # ✅ 2. ถ้าไม่ซ้ำ ให้ทำการบันทึก
        mongo.db.students.insert_one({
            "student_id": data.get('student_id'), # เลขที่ (รัน 1-5 ตามห้อง)
            "nickname": data.get('nickname'),
            "fullname": fullname,
            "grade": grade,
            "disability_type": data.get('disability_type'),
            "outstanding_subject": data.get('outstanding_subject'), # วิชาที่โดดเด่น
            "note": data.get('note'), # หมายเหตุ
            "technique": data.get('technique'),
            "timestamp": ObjectId()
        })
        return jsonify({"success": True, "message": f"บันทึกข้อมูลของ {fullname} สำเร็จครับ!"})
        
    except Exception as e:
        print(f"❌ Add Student Error: {str(e)}")
        return jsonify({"success": False, "message": f"เกิดข้อผิดพลาด: {str(e)}"}), 500
        
# -----------------------------------------------------------------------------
# 7. AI CHAT SYSTEM (GEMINI-3.1-PRO-PREVIEW)
# -----------------------------------------------------------------------------

@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    """ ส่งคำถามไปยัง AI โดยใช้ Gemini 3.1 Pro Preview พร้อม Template IEP และบริบทนักเรียน 200 คน """
    user_input = request.json.get('message')
    
    try:
        # 1. ดึงข้อมูลนักเรียนทั้งหมด (รองรับถึง 200 คนตามที่พี่เตรียมไว้)
        # ดึงฟิลด์ fullname, grade และ technique (ที่รวมจุดอ่อน/จุดเด่น/หมายเหตุไว้แล้ว)
        students = list(mongo.db.students.find().limit(200))
        
        # สร้างบริบทข้อมูลนักเรียนให้ AI (Context)
        ctx = "\n".join([
            f"- {s.get('fullname')} (ชั้น {s.get('grade')}) | ข้อมูล: {s.get('technique')}" 
            for s in students
        ])

        # 2. กำหนด Template การตอบ IEP (พี่สามารถปรับแก้ข้อความในนี้ได้ตามใจชอบ)
        iep_template = """
        โครงสร้างการตอบแผน IEP:
        ---
        📌 ข้อมูลนักเรียน: [ระบุชื่อ-นามสกุล และชั้นเรียน]
        🔍 วิเคราะห์ปัญหา (จุดที่ควรพัฒนา): [สรุปจากวิชาที่บกพร่อง]
        🌟 จุดแข็ง/ความสามารถพิเศษ: [สรุปจากวิชาที่โดดเด่น]
        💡 แนวทางการช่วยเหลือ/เทคนิคการสอน: [ระบุเป็นข้อๆ ให้ครูนำไปใช้ได้จริง]
        📝 ข้อควรระวัง/หมายเหตุ: [ดึงมาจากหมายเหตุในระบบ]
        ---
        """

        # 3. สร้าง Prompt ที่สมบูรณ์ (System Instruction + Context + User Input)
        prompt = (
            f"คุณคือผู้เชี่ยวชาญด้านการศึกษาพิเศษและการจัดทำแผน IEP (Individualized Education Program)\n"
            f"กรุณาใช้ข้อมูลนักเรียนด้านล่างนี้เพื่อตอบคำถาม และต้องตอบตามรูปแบบ Template นี้เท่านั้น:\n"
            f"{iep_template}\n\n"
            f"รายชื่อนักเรียนในระบบ:\n{ctx}\n\n"
            f"คำถามจากคุณครู: {user_input}"
        )

        # 4. เรียกใช้ API Gemini 3.1 Pro Preview (ตั้ง Timeout เผื่อรุ่น Pro คิดนาน)
        res = requests.post(
            f"{AI_BASE_URL}/chat/completions", 
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            }, 
            json={
                "model": "gemini-3.1-pro-preview",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4, # ปรับให้นิ่งเพื่อความแม่นยำของข้อมูล
                "top_p": 0.9
            }, 
            timeout=90 # ขยายเวลาเป็น 90 วินาทีสำหรับรุ่น Pro
        )
        
        if res.status_code == 200:
            result_json = res.json()
            # ตรวจสอบโครงสร้าง response จาก API มข.
            if 'choices' in result_json and len(result_json['choices']) > 0:
                reply = result_json['choices'][0]['message']['content']
                return jsonify({"reply": reply})
            else:
                return jsonify({"reply": "AI ตอบกลับมาในรูปแบบที่ไม่ถูกต้อง"}), 500
        else:
            print(f"❌ AI API Error: {res.status_code} - {res.text}")
            return jsonify({"reply": f"AI ขัดข้อง (Error: {res.status_code}) กรุณาลองใหม่ครับ"}), res.status_code

    except requests.exceptions.Timeout:
        return jsonify({"reply": "AI ใช้เวลาประมวลผลนานเกินไป (Timeout) กรุณาลองใหม่หรือลดขนาดคำถามครับ"}), 504
    except Exception as e:
        print(f"❌ Ask AI Error: {str(e)}")
        return jsonify({"reply": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"}), 500

# -----------------------------------------------------------------------------
# 8. PAGE NAVIGATION (การเข้าถึงหน้าแสดงผลข้อมูล)
# -----------------------------------------------------------------------------

@app.route('/chatbot')
@login_required
def chatbot_page():
    """ หน้าสำหรับใช้งาน AI Chatbot """
    return render_template('chatbot.html') 

@app.route('/student_list')
@login_required
def student_list_page():
    """ หน้าแสดงรายชื่อนักเรียนโดยกรองตามสิทธิ์การเข้าถึงของผู้ใช้งาน """
    username = session.get('username')
    permission = session.get('permission')
    
    # ✅ ถ้าเป็น Admin หรือ Super Admin ให้เห็นข้อมูลนักเรียนทั้งหมด
    if permission in ['Admin', 'Super Admin']:
        students = list(mongo.db.students.find().sort("fullname", 1))
    else:
        # ✅ ถ้าเป็นคุณครู ให้เห็นเฉพาะชั้นเรียนที่ได้รับมอบสิทธิ์ (Grant Access) ไว้เท่านั้น
        access_list = list(mongo.db.user_access.find({"username": username}))
        allowed_grades = [acc.get('accessible_grade') for acc in access_list if acc.get('accessible_grade')]
        
        # ค้นหานักเรียนที่อยู่ในชั้นเรียนที่คุณครูมีสิทธิ์
        students = list(mongo.db.students.find({"grade": {"$in": allowed_grades}}).sort("fullname", 1))
        
    return render_template('student_list.html', students=students)

@app.route('/setting_page')
@login_required
def setting_page():
    """ หน้าสำหรับตั้งค่าโปรไฟล์ส่วนตัว """
    return render_template('setting.html')

@app.route('/clear_students')
@login_required
@admin_required
def clear_students():
    """ Route พิเศษสำหรับล้างข้อมูลนักเรียนทั้งหมดในกรณีที่มีข้อมูลขยะจำนวนมาก """
    count = mongo.db.students.delete_many({})
    return f"ล้างข้อมูลนักเรียนสำเร็จ! ลบไปทั้งหมด {count.deleted_count} รายการ เพื่อเริ่มนำเข้าข้อมูลใหม่ที่ถูกต้อง"

# -----------------------------------------------------------------------------
# START APPLICATION (เริ่มต้นการทำงานของแอปพลิเคชัน)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # รันบนเครื่องตัวเองที่พอร์ต 8000
    app.run(debug=True, host='0.0.0.0', port=8000)