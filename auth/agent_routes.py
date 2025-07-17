from flask import Blueprint, request, render_template, redirect, url_for, session
import sqlite3
from datetime import datetime

agent_auth = Blueprint("agent_auth", __name__)
DB_PATH = 'database/bikow.db'

# Agent Registration
@agent_auth.route("/agent/register", methods=["GET", "POST"])
def register_agent():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        vehicle = request.form["vehicle"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO agents (name, email, phone, password, vehicle) VALUES (?, ?, ?, ?, ?)",
                      (name, email, phone, password, vehicle))
            conn.commit()
            return "✅ Registration submitted. Wait for admin verification."
        except sqlite3.IntegrityError:
            return "⚠️ Agent already exists with this phone."
        finally:
            conn.close()

    return render_template("pages/register_agent.html")

# Agent Login
@agent_auth.route("/agent/login", methods=["GET", "POST"])
def login_agent():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, is_verified FROM agents WHERE phone=? AND password=?", (phone, password))
        agent = c.fetchone()

        if agent:
            if agent[2] == 0:
                return "⏳ Not verified by admin yet."

            # Update last active timestamp
            c.execute("UPDATE agents SET last_active=? WHERE id=?", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), agent[0]))
            conn.commit()

            session["agent_id"] = agent[0]
            session["agent_name"] = agent[1]
            conn.close()
            return redirect(url_for("agent_dashboard"))
        conn.close()
        return "❌ Invalid credentials."

    return render_template("pages/login_agent.html")

# Agent Dashboard
@agent_auth.route("/agent/dashboard")
def agent_dashboard():
    if "agent_id" not in session:
        return redirect(url_for("agent_auth.login_agent"))

    agent_id = session["agent_id"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, email, phone, vehicle, is_verified, total_deliveries, last_active FROM agents WHERE id=?", (agent_id,))
    agent = c.fetchone()

    c.execute("SELECT * FROM deliveries WHERE phone=(SELECT phone FROM agents WHERE id=?) ORDER BY id DESC", (agent_id,))
    deliveries = c.fetchall()

    conn.close()
    return render_template("pages/agent_dashboard.html", agent=agent, deliveries=deliveries)

# Agent Profile View (Public)
@agent_auth.route("/agent/profile/<int:agent_id>")
def view_agent_profile(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, email, phone, vehicle, total_deliveries, last_active FROM agents WHERE id=?", (agent_id,))
    agent = c.fetchone()

    c.execute("SELECT rating, comment, timestamp FROM ratings WHERE agent_id=? ORDER BY id DESC", (agent_id,))
    ratings = c.fetchall()
    conn.close()

    return render_template("pages/agent_profile.html", agent=agent, ratings=ratings)

# Submit a Rating
@agent_auth.route("/agent/rate/<int:agent_id>", methods=["GET", "POST"])
def rate_agent(agent_id):
    if request.method == "POST":
        rating = int(request.form["rating"])
        comment = request.form.get("comment", "")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO ratings (agent_id, rating, comment, timestamp) VALUES (?, ?, ?, ?)",
                  (agent_id, rating, comment, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for("agent_auth.view_agent_profile", agent_id=agent_id))

    return render_template("pages/rate_agent.html", agent_id=agent_id)

