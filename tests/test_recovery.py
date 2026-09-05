import unittest
from datetime import datetime, timezone

from gridpulse.health import HealthResult, HealthStatus
from gridpulse.recovery import RecoveryTracker


NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def health(status):
    return HealthResult(score=100 if status is HealthStatus.HEALTHY else 60, status=status, signals={})


class RecoveryTrackerTests(unittest.TestCase):
    def test_initial_healthy_state_is_not_recovery(self):
        result = RecoveryTracker().evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        self.assertFalse(result["recovered"])
        self.assertEqual(0, result["recovery_count"])
        self.assertIsNone(result["last_recovered_at"])

    def test_stale_to_healthy_records_recovery(self):
        tracker = RecoveryTracker()
        tracker.evaluate("asset-1", health(HealthStatus.STALE), NOW)
        result = tracker.evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        self.assertTrue(result["recovered"])
        self.assertEqual(1, result["recovery_count"])
        self.assertEqual(NOW.isoformat(), result["last_recovered_at"])

    def test_degraded_to_healthy_records_recovery(self):
        tracker = RecoveryTracker()
        tracker.evaluate("asset-1", health(HealthStatus.DEGRADED), NOW)
        result = tracker.evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        self.assertTrue(result["recovered"])
        self.assertEqual(1, result["recovery_count"])

    def test_repeated_healthy_evaluation_does_not_double_count(self):
        tracker = RecoveryTracker()
        tracker.evaluate("asset-1", health(HealthStatus.FAILED), NOW)
        tracker.evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        result = tracker.evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        self.assertFalse(result["recovered"])
        self.assertEqual(1, result["recovery_count"])

    def test_assets_are_tracked_independently(self):
        tracker = RecoveryTracker()
        tracker.evaluate("asset-1", health(HealthStatus.STALE), NOW)
        tracker.evaluate("asset-2", health(HealthStatus.HEALTHY), NOW)
        recovered = tracker.evaluate("asset-1", health(HealthStatus.HEALTHY), NOW)
        untouched = tracker.evaluate("asset-2", health(HealthStatus.HEALTHY), NOW)
        self.assertEqual(1, recovered["recovery_count"])
        self.assertEqual(0, untouched["recovery_count"])


if __name__ == "__main__":
    unittest.main()
