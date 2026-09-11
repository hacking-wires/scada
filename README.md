# SCADA Attack Simulation & Detection

A minimal Flask-based SCADA monitor plus a set of attack scripts, built to demonstrate two classes of attack against industrial telemetry:

1. **Spoof** — voltage/current/temperature values pushed outside safe operating thresholds.
2. **DoS** — request bursts above a per-second rate cap.

Both are detected server-side, rejected with `HTTP 403`, and streamed to a live dashboard.

## Components

| File | Role |
|---|---|
| `server.py` | Flask app: ingest at `POST /data`, status at `GET /status`, dashboard at `GET /`. Threshold + rate detection. |
| `simulator.py` | Sends healthy readings once per second (baseline traffic). |
| `attacks/spoof.py` | Injects out-of-range readings. |
| `attacks/dos.py` | Concurrent flood to trip the rate cap. |
| `templates/monitor.html` | Live dashboard: latest values, alert, recent attacks, traffic chart. |
| `tests/test_server.py` | Flask test-client end-to-end tests. |

## Detection rules

- **Voltage** must be in `[190.0, 280.0]`
- **Current** must be in `[2.0, 12.0]`
- **Temperature** must be in `[5.0, 70.0]`
- **Request rate** capped at `20 req/s` per rolling second

Tunable at the top of `server.py` (`THRESHOLDS`, `MAX_REQ_PER_SECOND`).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# terminal 1 — start the monitor
python server.py                 # http://127.0.0.1:5000

# terminal 2 — healthy baseline traffic
python simulator.py
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) — you'll see live voltage / current / temperature and a traffic chart.

## Trigger the attacks

```bash
# In a third terminal
python attacks/spoof.py          # out-of-range values → SPOOF entries in the log
python attacks/dos.py            # ~100 req/s flood → DoS Detected entries
```

Both show up in the dashboard's **Recent Attacks** panel within a second.

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers: normal readings accepted, status reflects the latest reading, spoof logged + rejected, DoS trips the rate cap, unknown fields ignored.

## API

| Method | Path | Body | Purpose |
|---|---|---|---|
| POST | `/data` | `{voltage, current, temperature}` | Ingest reading, run detection |
| GET | `/status` | – | Latest values, alert, last 5 attacks, current traffic |
| GET | `/` | – | Dashboard |
| POST | `/reset` | – | Clear in-memory state (useful for tests / demos) |

## Notes

This is a teaching demo, not a production SCADA stack. State is in-memory and reset on restart. Do not point it at real ICS traffic.
