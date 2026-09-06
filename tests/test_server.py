"""Tests for the SCADA monitor.

Import the module fresh in each test so the in-module state
(`data_store`, `request_log`, `alerts`, `attack_log`) starts empty.
"""
import importlib
import sys

import pytest


@pytest.fixture
def client():
    if "server" in sys.modules:
        del sys.modules["server"]
    server = importlib.import_module("server")
    server.app.config["TESTING"] = True
    return server.app.test_client(), server


def _post(client, payload):
    return client.post("/data", json=payload)


def test_in_range_reading_is_normal(client):
    c, _ = client
    r = _post(c, {"voltage": 230, "current": 5, "temperature": 25})
    assert r.status_code == 200
    assert r.get_json()["message"] == "Normal"


def test_out_of_range_voltage_flags_alert(client):
    c, server = client
    r = _post(c, {"voltage": 300, "current": 5, "temperature": 25})
    assert r.status_code == 403
    assert "VOLTAGE out of range" in r.get_json()["message"]
    assert len(server.alerts) == 1


def test_dashboard_status_reflects_latest_reading(client):
    """Regression test for the data_store bug — /status must expose the
    last reading, not '--'."""
    c, _ = client
    _post(c, {"voltage": 231.5, "current": 4.2, "temperature": 22.0})
    body = c.get("/status").get_json()
    assert body["voltage"] == 231.5
    assert body["current"] == 4.2
    assert body["temperature"] == 22.0


def test_out_of_range_reading_still_appears_on_dashboard(client):
    """Spoofed values must reach the dashboard so operators see the attack."""
    c, _ = client
    _post(c, {"voltage": 300, "current": 5, "temperature": 25})
    body = c.get("/status").get_json()
    assert body["voltage"] == 300


def test_dos_detection_after_burst(client):
    c, server = client
    for _ in range(server.MAX_REQ_PER_SECOND + 5):
        r = _post(c, {"voltage": 230, "current": 5, "temperature": 25})
    assert r.status_code == 403
    assert r.get_json()["message"] == "DoS Detected"
    assert any("DoS Detected" in entry for entry in server.attack_log)


def test_malformed_json_does_not_crash(client):
    c, _ = client
    r = c.post("/data", data="not json at all", content_type="application/json")
    assert r.status_code == 200
    assert r.get_json()["message"] == "Normal"


def test_status_empty_before_any_data(client):
    c, _ = client
    body = c.get("/status").get_json()
    assert body["voltage"] == "--"
    assert body["logs"] == []
