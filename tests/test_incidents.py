import unittest

from gridpulse.incidents import IncidentController, IncidentType
from gridpulse.simulator import FleetSimulator


class IncidentControllerTests(unittest.TestCase):
    def test_incident_lifecycle(self):
        controller = IncidentController()
        controller.activate("aurora-1", IncidentType.HIGH_TEMPERATURE)
        self.assertEqual(1, len(controller.list()))
        controller.clear("aurora-1")
        self.assertEqual([], controller.list())

    def test_incident_only_changes_target_asset(self):
        assets = FleetSimulator().snapshot()
        original = assets[1].points["temperature"].value
        controller = IncidentController()
        controller.activate(assets[0].asset_id, IncidentType.HIGH_TEMPERATURE)
        controller.apply(assets)
        self.assertEqual(72.0, assets[0].points["temperature"].value)
        self.assertEqual(original, assets[1].points["temperature"].value)


if __name__ == "__main__":
    unittest.main()
