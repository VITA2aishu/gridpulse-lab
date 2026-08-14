from datetime import datetime, timedelta, timezone
import unittest

from gridpulse.incidents import IncidentController, IncidentType
from gridpulse.models import Quality
from gridpulse.quality import QualityEngine
from gridpulse.simulator import FleetSimulator


class QualityEngineTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.asset = FleetSimulator().snapshot(self.now)[0]
        self.engine = QualityEngine(stale_after=timedelta(seconds=10))

    def test_fresh_nominal_points_are_good(self):
        self.engine.evaluate(self.asset, self.now)
        self.assertTrue(all(point.quality is Quality.GOOD for point in self.asset.points.values()))

    def test_old_points_become_stale(self):
        IncidentController().apply([self.asset])
        self.asset.points["soc"].timestamp -= timedelta(seconds=11)
        self.engine.evaluate(self.asset, self.now)
        self.assertEqual(Quality.STALE, self.asset.points["soc"].quality)

    def test_missing_soc_is_detected(self):
        controller = IncidentController()
        controller.activate(self.asset.asset_id, IncidentType.MISSING_SOC)
        controller.apply([self.asset])
        self.engine.evaluate(self.asset, self.now)
        self.assertEqual(Quality.MISSING, self.asset.points["soc"].quality)

    def test_frequency_excursion_is_bad(self):
        controller = IncidentController()
        controller.activate(self.asset.asset_id, IncidentType.BAD_FREQUENCY)
        controller.apply([self.asset])
        self.engine.evaluate(self.asset, self.now)
        self.assertEqual(Quality.BAD, self.asset.points["frequency"].quality)


if __name__ == "__main__":
    unittest.main()

