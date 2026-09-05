import unittest
from datetime import datetime, timedelta, timezone

from gridpulse.health import HealthEngine, HealthStatus
from gridpulse.models import AssetTelemetry, Quality, TelemetryPoint


NOW = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def make_asset(*, age_seconds=1, quality=Quality.GOOD):
    return AssetTelemetry(
        asset_id="test-1",
        name="Test Asset",
        region="test",
        capacity_mw=10,
        energy_mwh=20,
        points={
            "soc": TelemetryPoint(
                value=50,
                unit="%",
                timestamp=NOW - timedelta(seconds=age_seconds),
                quality=quality,
            ),
            "frequency": TelemetryPoint(
                value=60.0,
                unit="Hz",
                timestamp=NOW - timedelta(seconds=age_seconds),
                quality=quality,
            ),
        },
    )


class HealthEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = HealthEngine()

    def test_healthy_asset(self):
        result = self.engine.evaluate(make_asset(), {"status": "progressing"}, NOW)
        self.assertEqual(100, result.score)
        self.assertEqual(HealthStatus.HEALTHY, result.status)
        self.assertEqual("fresh", result.signals["freshness"])
        self.assertEqual("available", result.signals["connectivity"])

    def test_bad_quality_degrades_asset(self):
        result = self.engine.evaluate(
            make_asset(quality=Quality.BAD),
            {"status": "progressing"},
            NOW,
        )
        self.assertEqual(HealthStatus.DEGRADED, result.status)
        self.assertEqual("bad", result.signals["data_quality"])

    def test_old_telemetry_is_stale(self):
        result = self.engine.evaluate(
            make_asset(age_seconds=60),
            {"status": "progressing"},
            NOW,
        )
        self.assertEqual(HealthStatus.STALE, result.status)
        self.assertEqual("stale", result.signals["freshness"])

    def test_frozen_progression_is_stale(self):
        result = self.engine.evaluate(make_asset(), {"status": "frozen"}, NOW)
        self.assertEqual(HealthStatus.STALE, result.status)
        self.assertEqual("frozen", result.signals["progression"])

    def test_empty_asset_is_failed(self):
        asset = make_asset()
        asset.points = {}
        result = self.engine.evaluate(asset, {"status": "progressing"}, NOW)
        self.assertEqual(0, result.score)
        self.assertEqual(HealthStatus.FAILED, result.status)
        self.assertEqual("unavailable", result.signals["connectivity"])


if __name__ == "__main__":
    unittest.main()
