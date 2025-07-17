import requests

def send_sms(phone, message):
    # Example using https://www.africastalking.com/
    api_key = 'YOUR_AT_API_KEY'
    sender = 'BikowTrade'
    url = 'https://api.africastalking.com/version1/messaging'

    headers = {
        'apiKey': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = {
        'username': 'YOUR_AT_USERNAME',
        'to': phone,
        'message': message,
        'from': sender
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        print(response.text)
    except Exception as e:
        print("SMS error:", e)
