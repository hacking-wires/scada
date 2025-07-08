import requests
import random
import time

URL = "http://127.0.0.1:5000/data"

while True:
    payload = {
        "voltage": round(random.uniform(180, 290), 2),
        "current": round(random.uniform(1, 15), 2),
        "temperature": round(random.uniform(0, 100), 2)
    }

    try:
        res = requests.post(URL, json=payload)
        print(f"Sent: {payload} | Status: {res.status_code}, Message: {res.json()['message']}")
    except Exception as e:
        print(f"Error sending data: {e}")
    
    time.sleep(1)  # 1 second interval
