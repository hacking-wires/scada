"""DoS attack: hammer /data with concurrent requests to trip the rate cap.

Server rate cap defaults to 20 req/s; this fires ~100 req/s across threads.
Expect to see HTTP 403 "DoS Detected" responses in the output.
"""

import concurrent.futures
import time

import requests

URL = "http://127.0.0.1:5000/data"
DURATION_SEC = 5
CONCURRENCY = 20
PAYLOAD = {"voltage": 230, "current": 6, "temperature": 30}


def hit():
    try:
        res = requests.post(URL, json=PAYLOAD, timeout=2)
        return res.status_code
    except requests.RequestException:
        return 0


def main():
    end = time.time() + DURATION_SEC
    counts = {200: 0, 403: 0, 0: 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        while time.time() < end:
            futures = [pool.submit(hit) for _ in range(CONCURRENCY)]
            for f in concurrent.futures.as_completed(futures):
                code = f.result()
                counts[code] = counts.get(code, 0) + 1
    print(f"done - accepted: {counts.get(200, 0)}  blocked: {counts.get(403, 0)}  errors: {counts.get(0, 0)}")


if __name__ == "__main__":
    main()
