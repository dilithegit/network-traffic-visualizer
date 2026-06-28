import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


class CaptureControlTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_stop_capture_endpoint_returns_success(self):
        response = self.client.post("/capture/stop")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["running"], False)
        self.assertTrue(response.get_json()["success"])

    def test_capture_status_endpoint_reports_stopped_state(self):
        response = self.client.get("/capture/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["running"], False)


if __name__ == "__main__":
    unittest.main()
