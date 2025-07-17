# payment_gateway.py
# This module integrates Mobile Money APIs (ClickPesa), manual confirmation & COD logic

import requests

# Config for real API keys from ClickPesa or Africa's Talking (to be stored securely)
CLICKPESA_API_KEY = "your_real_clickpesa_api_key"
CLICKPESA_BASE_URL = "https://api.clickpesa.com/payments"

# Supported methods to show dynamically in frontend
SUPPORTED_METHODS = [
    {"name": "M-Pesa", "code": "mpesa"},
    {"name": "Tigo Pesa", "code": "tigopesa"},
    {"name": "HaloPesa", "code": "halopesa"},
    {"name": "Airtel Money", "code": "airtelmoney"},
    {"name": "EazyPesa", "code": "eazypesa"},
    {"name": "Manual Payment", "code": "manual"},
    {"name": "Cash on Delivery", "code": "cod"},
]

def initiate_payment(phone, amount, method):
    """Start payment via mobile money aggregator API like ClickPesa."""
    if method not in [m["code"] for m in SUPPORTED_METHODS]:
        return {"error": "Unsupported method"}

    payload = {
        "amount": amount,
        "currency": "TZS",
        "payment_method": method,
        "phone_number": phone,
        "reference": f"ORDER-{phone[-4:]}"
    }
    headers = {"Authorization": f"Bearer {CLICKPESA_API_KEY}"}

    try:
        res = requests.post(CLICKPESA_BASE_URL, json=payload, headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def record_manual_payment(name, phone, amount, code):
    """Used when user pays via *150# manually and enters control no."""
    from datetime import datetime
    import sqlite3

    conn = sqlite3.connect("database/bikow.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, amount TEXT,
            code TEXT, method TEXT DEFAULT 'manual', timestamp TEXT
        )
    """)
    c.execute("INSERT INTO payments (name, phone, amount, code, timestamp) VALUES (?, ?, ?, ?, ?)",
              (name, phone, amount, code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    return True

def mark_cod_order(user_id, amount):
    """Used when a user selects Cash on Delivery and places order."""
    import sqlite3
    from datetime import datetime
    conn = sqlite3.connect("database/bikow.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cod_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TEXT
        )
    """)
    c.execute("INSERT INTO cod_orders (user_id, amount, timestamp) VALUES (?, ?, ?)",
              (user_id, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return True
