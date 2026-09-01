from datetime import datetime, timedelta, timezone
import unittest

from gridpulse.lag import processing_lag_seconds
from gridpulse.models import AssetTelemetry, TelemetryPoint


class ProcessingLagTests(unittest.TestCase):
    def asset_at(self, timestamp):
        return AssetTelemetry(
            asset_id="test-1",
            name="Synthetic Asset",
            region="test",
            capacity_mw=10.0,
            energy_mwh=20.0,
            points={"mw": TelemetryPoint(5.0, "MW", timestamp)},
        )

    def test_processing_lag_uses_newest_observation(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        asset = self.asset_at(now - timedelta(seconds=2.5))
        self.assertEqual(2.5, processing_lag_seconds(asset, now))

    def test_processing_lag_never_goes_negative(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        asset = self.asset_at(now + timedelta(seconds=1))
        self.assertEqual(0.0, processing_lag_seconds(asset, now))


if __name__ == "__main__":
    unittest.main()
