# 📄 utils/email_sender.py

import smtplib
from email.mime.text import MIMEText

GMAIL_USER = "brianossei161@gmail.com"
GMAIL_PASS = "ekvjilngpynslnbb"  # Example you used before

def send_email(to, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
