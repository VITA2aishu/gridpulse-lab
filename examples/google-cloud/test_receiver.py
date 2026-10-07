import contextlib
import io
import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from wsgiref.simple_server import make_server

from receiver import MAX_BODY_BYTES, QuietHandler, application


class ReceiverTests(unittest.TestCase):
    def call(self, body=b"{}", **overrides):
        env = {"PATH_INFO": "/telemetry", "REQUEST_METHOD": "POST", "CONTENT_TYPE": "application/json",
               "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body)}
        env.update(overrides)
        response = {}
        def start(status, headers):
            response.update(status=int(status.split()[0]), headers=dict(headers))
        logs = io.StringIO()
        with contextlib.redirect_stdout(logs):
            response["body"] = json.loads(b"".join(application(env, start)))
        response["logs"] = [json.loads(line) for line in logs.getvalue().splitlines()]
        return response

    def event(self, age=0, value=1):
        return json.dumps({"source_id": "demo-a", "event_time": (datetime.now(timezone.utc)-timedelta(seconds=age)).isoformat(), "value": value}).encode()

    def test_classification_http_contract(self):
        for age, value, code, status in ((0, 1, 200, "fresh"), (120, 1, 200, "late"), (-30, 1, 200, "future"), (0, "bad", 422, "invalid")):
            with self.subTest(status=status):
                result = self.call(self.event(age, value))
                self.assertEqual(result["status"], code)
                self.assertEqual(result["body"]["status"], status)
                self.assertEqual(result["logs"][0]["status"], status)

    def test_routes_methods_health_and_headers(self):
        result = self.call(PATH_INFO="/healthz", REQUEST_METHOD="GET")
        self.assertEqual(result["body"]["checks"], "process_only")
        self.assertEqual(result["headers"]["Cache-Control"], "no-store")
        self.assertEqual(self.call(REQUEST_METHOD="GET")["status"], 405)
        self.assertEqual(self.call(PATH_INFO="/other")["status"], 404)

    def test_body_and_media_limits(self):
        self.assertEqual(self.call(CONTENT_TYPE="text/plain")["status"], 415)
        for length in ("", "-1", "oops", "9"*100):
            self.assertEqual(self.call(CONTENT_LENGTH=length)["status"], 411)
        self.assertEqual(self.call(b"x"*(MAX_BODY_BYTES+1))["status"], 413)
        self.assertEqual(self.call(b"{}", CONTENT_LENGTH="3")["status"], 400)

    def test_json_and_schema_rejections(self):
        for body in (b"[", b"\xff", b"[]", b'{"value":NaN}', b'{"value":1,"value":2}', b"["*1200+b"]"*1200):
            self.assertEqual(self.call(body)["status"], 400)
        event = json.loads(self.event())
        event["extra"] = "unexpected"
        self.assertEqual(self.call(json.dumps(event).encode())["status"], 400)

    def test_no_raw_payload_or_credentials_in_logs(self):
        secret = "example-secret-not-a-real-credential"
        result = self.call(json.dumps({"token": secret}).encode(), HTTP_AUTHORIZATION="Bearer "+secret, QUERY_STRING="token="+secret)
        self.assertNotIn(secret, json.dumps(result))

    def test_real_http_round_trip(self):
        server = make_server("127.0.0.1", 0, application, handler_class=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}"
            with urllib.request.urlopen(url+"/healthz", timeout=3) as response:
                self.assertEqual(response.status, 200)
            request = urllib.request.Request(url+"/telemetry", data=self.event(), headers={"Content-Type": "application/json"})
            with contextlib.redirect_stdout(io.StringIO()):
                with urllib.request.urlopen(request, timeout=3) as response:
                    self.assertEqual(json.load(response)["status"], "fresh")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
