from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

data_store = []
request_log = []
alerts = []
attack_log = []

# Configurable thresholds
THRESHOLDS = {
    "voltage": (190.0, 280.0),
    "current": (2.0, 12.0),
    "temperature": (5.0, 70.0)
}

# Max allowed requests per second to detect DoS
MAX_REQ_PER_SECOND = 20

@app.route('/')
def index():
    return render_template("monitor.html")

@app.route('/data', methods=['POST'])
def receive_data():
    global request_log, alerts, attack_log

    data = request.get_json(silent=True) or {}
    timestamp = datetime.now()

    request_log = [t for t in request_log if t > timestamp - timedelta(seconds=1)]
    request_log.append(timestamp)

    status = 200
    message = "Normal"

    # Check for DoS attack
    if len(request_log) > MAX_REQ_PER_SECOND:
        status = 403
        message = "DoS Detected"
        attack_log.append(f"[{timestamp}] DoS Detected")
        return jsonify({"status": status, "message": message}), status

    # Record the reading so the dashboard can display it — including
    # out-of-range values, which are the evidence of a spoofing attack.
    data_store.append({**data, "timestamp": timestamp.isoformat()})

    # Threshold checks
    for param, value in data.items():
        min_val, max_val = THRESHOLDS.get(param, (None, None))
        if min_val is not None and (value < min_val or value > max_val):
            message = f"{param.upper()} out of range: {value}"
            alerts.append(f"[{timestamp}] {message}")
            status = 403

    return jsonify({"status": status, "message": message}), status

@app.route('/status', methods=['GET'])
def get_status():
    traffic = len(request_log)
    latest_data = data_store[-1] if data_store else {}
    return jsonify({
        "voltage": latest_data.get("voltage", "--"),
        "current": latest_data.get("current", "--"),
        "temperature": latest_data.get("temperature", "--"),
        "alert": alerts[-1] if alerts else "",
        "logs": attack_log[-5:],  # Last 5 logs
        "traffic": traffic
    })

if __name__ == '__main__':
    app.run(debug=True)
