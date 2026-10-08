"""Small WSGI telemetry receiver. Cloud Run IAM must enforce authentication.

Local development only: python examples/google-cloud/receiver.py
"""
import json
import os
import re
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from wsgiref.simple_server import WSGIRequestHandler, make_server

from telemetry_logs import classify

MAX_BODY_BYTES = 4096
ALLOWED_KEYS = {"source_id", "event_time", "value"}


def emit(record):
    print(json.dumps(record, allow_nan=False), flush=True)


def reject_constant(value):
    raise ValueError("Nonstandard JSON number")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def application(environ, start_response, *, observer=None):
    request_id = str(uuid.uuid4())

    def respond(code, payload, reason=None, extra_headers=()):
        if reason:
            # No raw payloads, headers, query strings or tokens in logs.
            emit({"severity": "WARNING", "component": "telemetry_receiver",
                  "message": "Request rejected", "reason": reason,
                  "request_id": request_id, "http_status": code})
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        start_response(f"{code} {HTTPStatus(code).phrase}", [
            ("Content-Type", "application/json"), ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
            ("X-Request-ID", request_id), *extra_headers])
        return [body]

    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "")
    if path not in ("/healthz", "/telemetry"):
        return respond(404, {"error": "not_found"})
    expected = "GET" if path == "/healthz" else "POST"
    if method != expected:
        return respond(405, {"error": "method_not_allowed"}, extra_headers=(("Allow", expected),))
    if path == "/healthz":
        return respond(200, {"status": "ready", "checks": "process_only"})
    if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
        return respond(415, {"error": "application_json_required"}, "content_type")
    raw_length = environ.get("CONTENT_LENGTH", "")
    if not re.fullmatch(r"[0-9]{1,10}", raw_length):
        return respond(411, {"error": "valid_content_length_required"}, "content_length")
    length = int(raw_length)
    if length > MAX_BODY_BYTES:
        return respond(413, {"error": "body_too_large"}, "body_limit")
    body = environ["wsgi.input"].read(length)
    if len(body) != length:
        return respond(400, {"error": "incomplete_body"}, "incomplete_body")
    try:
        event = json.loads(body.decode("utf-8"), parse_constant=reject_constant,
                           object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return respond(400, {"error": "invalid_json"}, "invalid_json")
    if not isinstance(event, dict) or set(event) != ALLOWED_KEYS:
        return respond(400, {"error": "exactly_source_id_event_time_value_required"}, "schema")
    timestamp = event["event_time"]
    if not isinstance(timestamp, str) or len(timestamp) > 64:
        return respond(400, {"error": "invalid_event_time"}, "timestamp")
    received_at = datetime.now(timezone.utc)
    record = classify(event, received_at)
    if observer is not None:
        observer(event, received_at)
    record.update(component="telemetry_receiver", request_id=request_id)
    emit(record)
    if record["status"] == "invalid":
        return respond(422, {"status": "invalid", "reason": record["reason"]})
    # A completed classification is successful even when data is late/future.
    return respond(200, {"status": record["status"], "event_age_seconds": record["event_age_seconds"]})


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass  # Avoid logging arbitrary URLs; application emits bounded records.


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    with make_server("127.0.0.1", port, application, handler_class=QuietHandler) as server:
        emit({"severity": "INFO", "component": "telemetry_receiver", "message": "Local demo ready", "port": port})
        server.serve_forever()
