"""
SCADA attack simulation & detection server.

POST /data     - ingest a sensor reading; runs threshold + rate checks
GET  /status   - latest reading + recent alerts + traffic for the dashboard
GET  /         - dashboard (monitor.html)
POST /reset    - clear state (useful for tests)
"""

from collections import deque
from datetime import datetime, timedelta
from threading import Lock

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------- state (in-memory, reset on restart) ------------------------------

_lock = Lock()
data_store: deque = deque(maxlen=500)   # (timestamp, reading dict)
request_log: deque = deque(maxlen=200)  # request timestamps for rate check
alerts: deque = deque(maxlen=100)       # threshold-breach strings
attack_log: deque = deque(maxlen=100)   # every detected attack (DoS + spoof)

# ---------- config -----------------------------------------------------------

THRESHOLDS = {
    "voltage":     (190.0, 280.0),
    "current":     (2.0,   12.0),
    "temperature": (5.0,   70.0),
}
MAX_REQ_PER_SECOND = 20


# ---------- routes -----------------------------------------------------------

@app.route("/")
def index():
    return render_template("monitor.html")


@app.route("/data", methods=["POST"])
def receive_data():
    payload = request.get_json(silent=True) or {}
    now = datetime.now()

    with _lock:
        # Rate limit window (last 1s)
        cutoff = now - timedelta(seconds=1)
        while request_log and request_log[0] < cutoff:
            request_log.popleft()
        request_log.append(now)

        # DoS check
        if len(request_log) > MAX_REQ_PER_SECOND:
            entry = f"[{now.isoformat()}] DoS Detected ({len(request_log)} req/s)"
            attack_log.append(entry)
            return jsonify({"status": 403, "message": "DoS Detected"}), 403

        # Record the reading so /status can show something real
        data_store.append((now, payload))

        # Threshold checks
        breaches = []
        for param, value in payload.items():
            lo, hi = THRESHOLDS.get(param, (None, None))
            if lo is None:
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                continue
            if v < lo or v > hi:
                msg = f"{param.upper()} out of range: {v}"
                breaches.append(msg)
                alerts.append(f"[{now.isoformat()}] {msg}")
                attack_log.append(f"[{now.isoformat()}] SPOOF: {msg}")

    if breaches:
        return jsonify({"status": 403, "message": "; ".join(breaches)}), 403
    return jsonify({"status": 200, "message": "Normal"}), 200


@app.route("/status", methods=["GET"])
def get_status():
    with _lock:
        latest = data_store[-1][1] if data_store else {}
        return jsonify({
            "voltage":     latest.get("voltage", "--"),
            "current":     latest.get("current", "--"),
            "temperature": latest.get("temperature", "--"),
            "alert":       alerts[-1] if alerts else "",
            "logs":        list(attack_log)[-5:],
            "traffic":     len(request_log),
        })


@app.route("/reset", methods=["POST"])
def reset():
    with _lock:
        data_store.clear()
        request_log.clear()
        alerts.clear()
        attack_log.clear()
    return jsonify({"status": "reset"}), 200


if __name__ == "__main__":
    app.run(debug=True)
