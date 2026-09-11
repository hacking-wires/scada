"""Normal-operation SCADA simulator.

Sends readings that mostly stay inside the safe operating envelope so the
dashboard shows a healthy baseline. Use attacks/*.py to inject anomalies.
"""

import random
import time

import requests

URL = "http://127.0.0.1:5000/data"

# stay comfortably inside THRESHOLDS in server.py
RANGES = {
    "voltage":     (210.0, 240.0),
    "current":     (4.0,   9.0),
    "temperature": (20.0,  55.0),
}


def next_reading():
    return {k: round(random.uniform(lo, hi), 2) for k, (lo, hi) in RANGES.items()}


def main():
    while True:
        payload = next_reading()
        try:
            res = requests.post(URL, json=payload, timeout=2)
            print(f"sent {payload} -> {res.status_code} {res.json()['message']}")
        except requests.RequestException as e:
            print(f"send failed: {e}")
        time.sleep(1)


if __name__ == "__main__":
    main()
