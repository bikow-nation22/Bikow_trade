# auth/email_sender.py

import smtplib
from email.mime.text import MIMEText

GMAIL_USER = "brianossei161@gmail.com"
GMAIL_PASS = "ekvjilngpynslnbb"

def send_otp_email(to_email, otp):
    subject = "Your OTP Code - Bikow Nation"
    body = f"Hi 👋,\n\nYour OTP code is: {otp}\n\nUse this to verify your account on Bikow Nation."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()
        print("✅ OTP email sent to", to_email)
    except Exception as e:
        print("❌ Failed to send email:", e)
