from datetime import datetime, timezone
import unittest

from gridpulse.simulator import FleetSimulator


class FleetSimulatorTests(unittest.TestCase):
    def test_snapshot_contains_three_fictional_assets(self):
        assets = FleetSimulator(seed=7).snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(3, len(assets))
        self.assertEqual({"aurora-1", "bluebonnet-1", "canyon-1"}, {a.asset_id for a in assets})

    def test_measurements_stay_inside_physical_limits(self):
        simulator = FleetSimulator(seed=9)
        for _ in range(50):
            for asset in simulator.snapshot():
                self.assertGreaterEqual(asset.points["soc"].value, 5)
                self.assertLessEqual(asset.points["soc"].value, 95)
                self.assertLessEqual(abs(asset.points["active_power"].value), asset.capacity_mw)

    def test_same_seed_produces_same_first_snapshot(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        left = FleetSimulator(seed=10).snapshot(now)
        right = FleetSimulator(seed=10).snapshot(now)
        self.assertEqual(left[0].to_dict(), right[0].to_dict())


if __name__ == "__main__":
    unittest.main()

