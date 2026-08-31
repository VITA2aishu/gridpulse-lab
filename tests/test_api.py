import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from gridpulse.server import GridPulseHandler


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GridPulseHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def raw_request(self, method, path, payload=None):
        connection = HTTPConnection("127.0.0.1", self.port)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        status = response.status
        content_type = response.getheader("Content-Type")
        connection.close()
        return status, content_type, content

    def request(self, method, path, payload=None):
        status, _, content = self.raw_request(method, path, payload)
        return status, json.loads(content) if content else {}

    def test_health_endpoint(self):
        status, body = self.request("GET", "/api/v1/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", body["status"])

    def test_telemetry_contract(self):
        status, body = self.request("GET", "/api/v1/telemetry")
        self.assertEqual(200, status)
        self.assertEqual(3, len(body["assets"]))
        self.assertIn("quality_summary", body)
        self.assertIn("progression_summary", body)
        self.assertIn("progression", body["assets"][0])
        self.assertIn(body["assets"][0]["progression"]["status"], {
            "progressing", "unchanged", "frozen"
        })

    def test_metrics_endpoint(self):
        status, content_type, content = self.raw_request("GET", "/metrics")
        text = content.decode()
        self.assertEqual(200, status)
        self.assertIn("text/plain", content_type)
        self.assertIn("gridpulse_telemetry_age_seconds", text)
        self.assertIn("gridpulse_active_alarms", text)
        self.assertIn("gridpulse_active_incidents", text)
        self.assertIn("gridpulse_quality_points", text)
        self.assertIn("gridpulse_progression_state", text)
        self.assertIn('asset_id="aurora-1"', text)

    def test_create_and_clear_incident(self):
        status, _ = self.request("POST", "/api/v1/incidents", {
            "asset_id": "aurora-1", "kind": "missing_soc"
        })
        self.assertEqual(201, status)
        status, body = self.request("GET", "/api/v1/incidents")
        self.assertEqual("missing_soc", body["incidents"][0]["kind"])
        status, _ = self.request("DELETE", "/api/v1/incidents/aurora-1")
        self.assertEqual(204, status)

    def test_frozen_stream_incident_is_supported(self):
        status, body = self.request("POST", "/api/v1/incidents", {
            "asset_id": "aurora-1", "kind": "frozen_stream"
        })
        self.assertEqual(201, status)
        self.assertEqual("frozen_stream", body["kind"])
        status, _ = self.request("DELETE", "/api/v1/incidents/aurora-1")
        self.assertEqual(204, status)

    def test_invalid_incident_returns_400(self):
        status, body = self.request("POST", "/api/v1/incidents", {"asset_id": "aurora-1"})
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", body["error"])


if __name__ == "__main__":
    unittest.main()
