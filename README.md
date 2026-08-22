# SCADA Attack Simulation & Detection

A minimal Flask-based SCADA monitor plus a traffic simulator, built to demonstrate two classes of attack against industrial telemetry:

1. **Out-of-range sensor spoofing** — voltage, current, or temperature values pushed outside safe operating thresholds.
2. **Denial of service** — bursts of requests above a per-second rate cap.

Both are logged and surfaced on a simple web dashboard.

## Components

| File | Role |
|---|---|
| `server.py` | Flask app: accepts `POST /data`, applies threshold + rate checks, serves the dashboard at `/`. |
| `simulator.py` | Sends randomized sensor readings to `/data` once per second. |
| `templates/monitor.html` | Live view of latest readings, alerts, and attack log. |

## Detection rules

- **Voltage** must be in `[190.0, 280.0]`
- **Current** must be in `[2.0, 12.0]`
- **Temperature** must be in `[5.0, 70.0]`
- **Request rate** capped at `20 req/s` — beyond that, requests are rejected as DoS.

Thresholds live in `THRESHOLDS` and `MAX_REQ_PER_SECOND` at the top of `server.py`.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# terminal 1 — start the monitor (http://127.0.0.1:5000)
python server.py

# terminal 2 — pump synthetic sensor data
python simulator.py
```

Open `http://127.0.0.1:5000/` to watch alerts appear as the simulator occasionally emits out-of-range values.

## Trying an attack

- **Spoof**: edit `simulator.py` to force `voltage = 300` — the monitor will flag it.
- **DoS**: run several `simulator.py` processes in parallel, or tighten the `time.sleep` — once you cross 20 req/s the server responds `403 DoS Detected` and the event lands in the attack log.

## Notes

This is a teaching demo, not a production SCADA stack. State is kept in-memory and reset on restart. Do not point it at real ICS traffic.
