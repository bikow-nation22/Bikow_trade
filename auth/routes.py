from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from models.user import (
    create_user, get_user_by_email_or_phone,
    set_user_otp, verify_user_otp, get_user_by_id
)
from auth.otp import generate_otp
from utils.email_sender import send_email
from datetime import datetime

auth = Blueprint("auth", __name__)

# ----------------- Register -----------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        provider = request.form['provider']
        paybill_number = request.form['paybill_number']

        existing_user = get_user_by_email_or_phone(email=email, phone=phone)
        if existing_user:
            return "⚠️ User already exists with this email or phone."

        otp = generate_otp()
        set_user_otp(email, otp)

        send_email(
            to=email,
            subject="Bikow Trade OTP Verification",
            message=f"Hi {name},\n\nYour OTP code is: {otp}"
        )

        create_user(
            name=name,
            email=email,
            phone=phone,
            password=password,
            provider=provider,
            paybill_number=paybill_number,
            otp=otp
        )

        session["verify_email"] = email
        return redirect(url_for("auth.verify_otp"))

    return render_template("pages/register.html")

# ----------------- Verify OTP -----------------
@auth.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_input = request.form['otp']
        user_id = session.get('pending_user_id')

        if not user_id:
            flash("No pending verification found.")
            return redirect(url_for('auth.register'))

        if verify_user_otp(user_id, otp_input):
            session['user'] = user_id
            flash("✅ Account verified and logged in.")
            return redirect(url_for('index'))
        else:
            flash("❌ Invalid OTP. Please try again.")

    return render_template("pages/verify_otp.html")

# ----------------- Login -----------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login']  # email or phone
        password = request.form['password']

        user = get_user_by_email_or_phone(login_input)

        if user and user['password'] == password:
            session['user'] = user['id']
            flash("✅ Login successful.")
            return redirect(url_for('index'))
        else:
            flash("❌ Invalid credentials.")

    return render_template("pages/login.html")

# ----------------- Logout -----------------
@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ----------------- Profile -----------------
@auth.route('/profile')
def profile():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = get_user_by_id(user_id)
    return render_template("pages/profile.html", user=user)

@auth.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    name = request.form['name']
    phone = request.form['phone']
    provider = request.form['provider']
    paybill_number = request.form['paybill_number']

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE users SET name=?, phone=?, provider=?, paybill_number=?
                 WHERE id=?""", (name, phone, provider, paybill_number, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("auth.profile"))
