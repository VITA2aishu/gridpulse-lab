"""Synthetic, deterministic structured logs; no cloud credentials required.

Run with Python 3.11+: python examples/google-cloud/telemetry_logs.py
Cloud Run integration is documented in docs/google-cloud-data-health.md.
"""
import json
import math
from datetime import datetime, timezone


def classify(event, received_at, max_age_seconds=60, future_tolerance_seconds=5):
    """Evaluate one arrival, not silence between arrivals or stream progression."""
    if received_at.tzinfo is None or received_at.utcoffset() is None:
        raise ValueError("received_at must be timezone-aware")
    for threshold in (max_age_seconds, future_tolerance_seconds):
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or threshold < 0:
            raise ValueError("thresholds must be finite nonnegative numbers")
    record = {"message": "Synthetic telemetry quality evaluation", "severity": "WARNING",
              "component": "telemetry_demo", "received_at": received_at.isoformat(),
              "status": "invalid", "reason": "invalid_schema"}
    if not isinstance(event, dict):
        return record
    if event.get("source_id") not in ("demo-a", "demo-b"):
        return record
    record["source_id"] = event["source_id"]
    value = event.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        record["reason"] = "invalid_value"
        return record
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        record["reason"] = "invalid_value"
        return record
    try:
        event_time = datetime.fromisoformat(event["event_time"].replace("Z", "+00:00"))
        if event_time.tzinfo is None or event_time.utcoffset() is None:
            raise ValueError("timezone missing")
    except (KeyError, AttributeError, TypeError, ValueError):
        record["reason"] = "invalid_event_time"
        return record
    age = (received_at - event_time).total_seconds()
    record.update(event_time=event_time.isoformat(), event_age_seconds=age)
    if age < -future_tolerance_seconds:
        record.update(status="future", reason="clock_or_timestamp_error")
    elif age > max_age_seconds:
        record.update(status="late", reason="event_age_exceeded")
    else:
        record.update(status="fresh", reason="within_age_limit", severity="INFO")
    return record


def demo_records():
    received = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
    for timestamp, value in (("2026-10-07T11:59:50Z", 10),
                             ("2026-10-07T11:58:00Z", 10),
                             ("2026-10-07T11:59:50Z", "bad"),
                             ("2026-10-07T12:00:30Z", 10)):
        yield classify({"source_id": "demo-a", "event_time": timestamp, "value": value}, received)


if __name__ == "__main__":
    for record in demo_records():
        print(json.dumps(record, allow_nan=False), flush=True)
