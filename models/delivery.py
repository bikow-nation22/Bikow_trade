import sqlite3

def get_delivery_by_id(delivery_id):
    conn = sqlite3.connect('database/db.sqlite3')  # adjust to your DB path
    cursor = conn.cursor()
    cursor.execute("SELECT id, agent_name FROM deliveries WHERE id=?", (delivery_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": row[0], "agent_name": row[1]}
    return None
