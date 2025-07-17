import requests
import base64
import datetime
import json

# === Your M-Pesa Sandbox Credentials ===
consumer_key = "NwOZQDcjWv7MUwo5HQP9XpHxFReO82zMGWolgB4pshaALA5W"
consumer_secret = "jH634glDJITbwNhLqaGDvceta9XDtGerbpXdZO7RN7uJWkwYzvAIS41l3ofAhwNV"
shortcode = "174379"
passkey = "JffjoXE/l3VUD6zFIQuS1udSnlw4+l+KtiNMLdI3FmY1Wqu1Bu/tWm1It47whqTO1NMjothObCbq2vGJ+d63LZaWLjVjVJ3ST41HTDnp6IeyB00g6BV1M8a/couaTTIgkt9pKzkEbwn9U1Mj99E6E0IUCJteodK1WatDxIMUvdbOZ2m4ZMowrQqQpBJe3DSDX8H3hpOMQIXybemwvGAqfxxqMB5OZRCvogl2lKSyK8zplKLbV/HxQwBWYUS/6CuFp5ibD1AAzvzIJ4a4t7Pxy0zMW/+rhdGdaQGspgtZyZDAPgJJ20lBNR9MD9gudZMAMnw7Vt8uKvPLGD+SNm7omQ=="

# === Helper: Get access token ===
def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    return response.json().get("access_token")

# === Helper: Get timestamp and password ===
def generate_password():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode("utf-8")
    return password, timestamp

# === Make STK Push ===
def lipa_na_mpesa(phone_number, amount):
    token = get_access_token()
    password, timestamp = generate_password()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://mydomain.com/callback",  # Replace or mock
        "AccountReference": "BikowTrade",
        "TransactionDesc": "Purchase at Bikow"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers, json=payload
    )
    return response.json()
