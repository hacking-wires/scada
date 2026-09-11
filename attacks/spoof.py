"""Spoof attack: inject out-of-range sensor readings.

Randomly picks voltage/current/temperature and pushes a value far outside
the safe operating envelope. The server should log each as a SPOOF attack.
"""

import random
import time

import requests

URL = "http://127.0.0.1:5000/data"

OUT_OF_RANGE = {
    "voltage":     [(50.0, 180.0), (290.0, 400.0)],
    "current":     [(0.0, 1.5),    (13.0, 30.0)],
    "temperature": [(-10.0, 4.0),  (75.0, 120.0)],
}


def spoof_payload():
    param = random.choice(list(OUT_OF_RANGE))
    lo, hi = random.choice(OUT_OF_RANGE[param])
    return {param: round(random.uniform(lo, hi), 2)}


def main():
    for _ in range(20):
        payload = spoof_payload()
        try:
            res = requests.post(URL, json=payload, timeout=2)
            print(f"spoof {payload} -> {res.status_code} {res.json()['message']}")
        except requests.RequestException as e:
            print(f"send failed: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
