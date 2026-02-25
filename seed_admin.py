import sqlite3
import os
from werkzeug.security import generate_password_hash

# ====== CONFIG ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "instance", "cola.db")

username = "DREAM".lower().strip()
password_plain = "1234"
displayname = "Super Admin"
permission = "Admin"

# ====== ตรวจสอบว่าโฟลเดอร์มีจริง ======
db_folder = os.path.dirname(DB)
os.makedirs(db_folder, exist_ok=True)

# ====== Hash Password ======
pw_hash = generate_password_hash(password_plain)

try:
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # ====== สร้างตารางถ้ายังไม่มี ======
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        displayname TEXT NOT NULL,
        permission TEXT
    )
    """)

    # ====== เช็คว่ามี user ซ้ำไหม ======
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        print("Username already exists.")
    else:
        cur.execute(
            "INSERT INTO users(username, password, displayname, permission) VALUES (?, ?, ?, ?)",
            (username, pw_hash, displayname, permission),
        )
        con.commit()
        print("Inserted admin successfully.")

    con.close()

except Exception as e:
    print("ERROR:", e)