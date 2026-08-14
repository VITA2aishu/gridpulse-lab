import unittest

from gridpulse.alarms import Severity, derive_alarms
from gridpulse.incidents import IncidentController, IncidentType
from gridpulse.quality import QualityEngine
from gridpulse.simulator import FleetSimulator


class AlarmTests(unittest.TestCase):
    def test_nominal_fleet_has_no_alarms(self):
        assets = FleetSimulator().snapshot()
        now = assets[0].points["soc"].timestamp
        for asset in assets:
            QualityEngine().evaluate(asset, now)
        self.assertEqual([], derive_alarms(assets))

    def test_bad_frequency_creates_critical_alarm(self):
        assets = FleetSimulator().snapshot()
        now = assets[0].points["soc"].timestamp
        controller = IncidentController()
        controller.activate(assets[0].asset_id, IncidentType.BAD_FREQUENCY)
        controller.apply(assets)
        for asset in assets:
            QualityEngine().evaluate(asset, now)
        alarms = derive_alarms(assets)
        self.assertEqual(1, len(alarms))
        self.assertEqual(Severity.CRITICAL, alarms[0].severity)
        self.assertEqual("frequency", alarms[0].point)


if __name__ == "__main__":
    unittest.main()
