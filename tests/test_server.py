"""End-to-end tests for the SCADA server (Flask test client, no network)."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import server  # noqa: E402


class ScadaTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        self.client.post("/reset")

    def _post(self, payload):
        return self.client.post("/data", data=json.dumps(payload),
                                content_type="application/json")

    def test_normal_reading_accepted(self):
        r = self._post({"voltage": 230, "current": 6, "temperature": 30})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["message"], "Normal")

    def test_status_reflects_latest_reading(self):
        self._post({"voltage": 231, "current": 6, "temperature": 30})
        s = self.client.get("/status").get_json()
        self.assertEqual(s["voltage"], 231)
        self.assertEqual(s["current"], 6)
        self.assertEqual(s["temperature"], 30)

    def test_spoof_logged_and_rejected(self):
        r = self._post({"voltage": 400, "current": 6, "temperature": 30})
        self.assertEqual(r.status_code, 403)
        s = self.client.get("/status").get_json()
        self.assertTrue(any("SPOOF" in line for line in s["logs"]))
        self.assertIn("VOLTAGE", s["alert"])

    def test_dos_trips_rate_cap(self):
        cap = server.MAX_REQ_PER_SECOND
        payload = {"voltage": 230, "current": 6, "temperature": 30}
        codes = [self._post(payload).status_code for _ in range(cap + 5)]
        self.assertIn(403, codes)
        s = self.client.get("/status").get_json()
        self.assertTrue(any("DoS" in line for line in s["logs"]))

    def test_unknown_field_ignored(self):
        r = self._post({"voltage": 230, "current": 6, "temperature": 30, "humidity": 999})
        self.assertEqual(r.status_code, 200)  # humidity has no threshold


if __name__ == "__main__":
    unittest.main()
