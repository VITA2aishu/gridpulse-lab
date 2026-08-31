import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ObservabilityExampleTests(unittest.TestCase):
    def test_grafana_dashboard_is_valid_json_with_expected_panels(self):
        path = ROOT / "examples" / "grafana" / "gridpulse-telemetry-health.json"
        dashboard = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual("GridPulse Lab - Telemetry Health", dashboard["title"])
        self.assertEqual("gridpulse-telemetry-health", dashboard["uid"])

        expressions = {
            target["expr"]
            for panel in dashboard["panels"]
            for target in panel.get("targets", [])
            if "expr" in target
        }
        self.assertIn("gridpulse_telemetry_age_seconds", expressions)
        self.assertIn("gridpulse_active_alarms", expressions)
        self.assertIn("gridpulse_active_incidents", expressions)
        self.assertIn("gridpulse_quality_points", expressions)
        self.assertIn("gridpulse_progression_state", expressions)

    def test_prometheus_example_scrapes_metrics_endpoint(self):
        path = ROOT / "examples" / "prometheus" / "prometheus.yml"
        content = path.read_text(encoding="utf-8")

        self.assertIn("job_name: gridpulse-lab", content)
        self.assertIn("metrics_path: /metrics", content)
        self.assertIn("127.0.0.1:8080", content)


if __name__ == "__main__":
    unittest.main()
