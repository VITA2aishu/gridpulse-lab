import unittest
from datetime import datetime, timedelta, timezone

from gridpulse.progression import ProgressionEngine
from gridpulse.simulator import FleetSimulator


class ProgressionTests(unittest.TestCase):
    def test_constant_value_with_new_observation_is_progressing(self):
        engine = ProgressionEngine(frozen_after=timedelta(seconds=5))
        simulator = FleetSimulator(seed=7)
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

        first = simulator.snapshot(t0)[0]
        first_result = engine.evaluate(first, t0)

        second = simulator.snapshot(t0 + timedelta(seconds=1))[0]
        for name, point in second.points.items():
            point.value = first.points[name].value
        second_result = engine.evaluate(second, t0 + timedelta(seconds=1))

        self.assertEqual("progressing", first_result["status"])
        self.assertEqual("progressing", second_result["status"])
        self.assertEqual(0.0, second_result["seconds_since_progress"])

    def test_repeated_observation_becomes_frozen_after_window(self):
        engine = ProgressionEngine(frozen_after=timedelta(seconds=5))
        simulator = FleetSimulator(seed=7)
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

        asset = simulator.snapshot(t0)[0]
        engine.evaluate(asset, t0)
        unchanged = engine.evaluate(asset, t0 + timedelta(seconds=3))
        frozen = engine.evaluate(asset, t0 + timedelta(seconds=6))

        self.assertEqual("unchanged", unchanged["status"])
        self.assertEqual("frozen", frozen["status"])
        self.assertEqual(6.0, frozen["seconds_since_progress"])

    def test_new_observation_recovers_from_frozen(self):
        engine = ProgressionEngine(frozen_after=timedelta(seconds=5))
        simulator = FleetSimulator(seed=7)
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

        first = simulator.snapshot(t0)[0]
        engine.evaluate(first, t0)
        self.assertEqual("frozen", engine.evaluate(first, t0 + timedelta(seconds=6))["status"])

        recovered = simulator.snapshot(t0 + timedelta(seconds=7))[0]
        result = engine.evaluate(recovered, t0 + timedelta(seconds=7))

        self.assertEqual("progressing", result["status"])
        self.assertEqual(0.0, result["seconds_since_progress"])


if __name__ == "__main__":
    unittest.main()
