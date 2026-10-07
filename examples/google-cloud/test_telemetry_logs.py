import unittest
from datetime import datetime, timezone
from telemetry_logs import classify, demo_records


class TelemetryLogTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
        self.event = {"source_id": "demo-a", "event_time": "2026-10-07T11:59:00Z", "value": 1}

    def test_scenarios(self):
        self.assertEqual([r["status"] for r in demo_records()], ["fresh", "late", "invalid", "future"])

    def test_age_boundary_and_timezone_equivalence(self):
        self.assertEqual(classify(self.event, self.now)["status"], "fresh")
        self.event["event_time"] = "2026-10-07T06:59:00-05:00"
        self.assertEqual(classify(self.event, self.now)["event_age_seconds"], 60)

    def test_invalid_values(self):
        for value in (True, None, "1", float("nan"), float("inf"), 10**1000):
            with self.subTest(value_type=type(value).__name__):
                self.event["value"] = value
                self.assertEqual(classify(self.event, self.now)["reason"], "invalid_value")

    def test_invalid_timestamps_and_schema(self):
        for value in (None, "bad", "2026-10-07T11:59:00"):
            self.event["event_time"] = value
            self.assertEqual(classify(self.event, self.now)["reason"], "invalid_event_time")
        self.assertEqual(classify([], self.now)["status"], "invalid")

    def test_invalid_configuration(self):
        for value in (-1, float("nan"), True):
            with self.assertRaises(ValueError):
                classify(self.event, self.now, max_age_seconds=value)
        with self.assertRaises(ValueError):
            classify(self.event, datetime(2026, 10, 7, 12))


if __name__ == "__main__":
    unittest.main()
