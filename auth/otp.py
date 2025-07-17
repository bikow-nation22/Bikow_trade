# 📄 auth/otp.py
import random

def generate_otp(length=4):
    return ''.join(random.choices("0123456789", k=length))
