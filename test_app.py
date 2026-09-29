import os
import json
import unittest
from app import app, load_incidents, save_incident

class TestRecallOps(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_homepage_loads(self):
        """Verify homepage loads with correct title and sections."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("RecallOps", html)
        self.assertIn("AI INCIDENT RESPONSE", html.upper())
        self.assertIn("RETAIN → RECALL → REASON → LEARN", html)
        self.assertIn("Close the Learning Loop", html)

    def test_api_status(self):
        """Verify live status endpoint returns JSON state."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("hindsight", data)
        self.assertIn("llm", data)
        self.assertEqual(data["hindsight"]["bank_id"], "recallops-demo")

    def test_analyze_validation(self):
        """Verify incident submission requires service and error."""
        res = self.client.post("/analyze", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("required", data["error"].lower())

    def test_resolve_validation(self):
        """Verify resolution submission requires root cause and resolution."""
        res = self.client.post("/resolve", json={"incident_id": "INC-001"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("required", data["error"].lower())

    def test_unconfigured_hindsight_useful_error(self):
        """Verify helpful error is returned without pretending memory worked."""
        # Ensure HINDSIGHT_API_KEY is unset for this test
        orig_key = os.environ.get("HINDSIGHT_API_KEY")
        if "HINDSIGHT_API_KEY" in os.environ:
            del os.environ["HINDSIGHT_API_KEY"]

        res = self.client.post("/seed")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("Hindsight connection failed", data["error"])
        self.assertIn("HINDSIGHT_API_KEY", data["error"])

        # Restore key if was set
        if orig_key is not None:
            os.environ["HINDSIGHT_API_KEY"] = orig_key

if __name__ == "__main__":
    unittest.main()
