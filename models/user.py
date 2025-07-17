import sqlite3
from flask_login import UserMixin

DB_PATH = "database/bikow.db"

def create_user(name, email, phone, password):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
            (name, email, phone, password)
        )
        conn.commit()

def get_user_by_email_or_phone(email, phone):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (email, phone))
        return cursor.fetchone()

def set_user_otp(phone, otp):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO user_otps (phone, otp) VALUES (?, ?)", (phone, otp))
        conn.commit()

def verify_user_otp(phone, otp):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp FROM user_otps WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        return row and row[0] == otp

def get_user_by_id(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

def get_paybill_details_by_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT provider, paybill_number FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"provider": row[0], "paybill_number": row[1]}
    return None
