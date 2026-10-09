import unittest
from datetime import datetime, timezone

from gridpulse.metrics import (
    OPENMETRICS_CONTENT_TYPE,
    PROMETHEUS_CONTENT_TYPE,
    _sample,
    negotiate_metrics_content_type,
    render_metrics,
)


class MetricsTests(unittest.TestCase):
    def test_sample_escapes_prometheus_label_values(self):
        """Prometheus labels must not let quotes, slashes, or newlines break a sample."""
        value = 'fictional "asset"\\line\nwest'

        self.assertEqual(
            'gridpulse_test{asset_id="fictional \\"asset\\"\\\\line\\nwest"} 1',
            _sample("gridpulse_test", 1, asset_id=value),
        )

    def test_openmetrics_payload_ends_with_eof_terminator(self):
        now = datetime.now(timezone.utc)

        plain = render_metrics([], {}, {}, 0, 0, now)
        openmetrics = render_metrics([], {}, {}, 0, 0, now, openmetrics=True)

        self.assertFalse(plain.endswith("# EOF\n"))
        self.assertTrue(openmetrics.endswith("# EOF\n"))
        self.assertTrue(openmetrics.startswith(plain))

    def test_content_type_defaults_to_prometheus_text(self):
        for accept in (None, "", "text/plain", "*/*", "application/json"):
            with self.subTest(accept=accept):
                self.assertEqual(
                    PROMETHEUS_CONTENT_TYPE,
                    negotiate_metrics_content_type(accept),
                )

    def test_content_type_negotiates_openmetrics(self):
        self.assertEqual(
            OPENMETRICS_CONTENT_TYPE,
            negotiate_metrics_content_type("application/openmetrics-text"),
        )

    def test_content_type_accepts_openmetrics_parameters(self):
        accept = (
            "application/openmetrics-text;version=1.0.0;escaping=allow-utf-8;q=0.9,"
            "text/plain;version=0.0.4;q=0.7"
        )
        self.assertEqual(OPENMETRICS_CONTENT_TYPE, negotiate_metrics_content_type(accept))

    def test_content_type_respects_plain_text_preference(self):
        accept = "application/openmetrics-text;q=0.2,text/plain;q=0.9"
        self.assertEqual(PROMETHEUS_CONTENT_TYPE, negotiate_metrics_content_type(accept))

    def test_content_type_ignores_rejected_openmetrics(self):
        accept = "application/openmetrics-text;q=0"
        self.assertEqual(PROMETHEUS_CONTENT_TYPE, negotiate_metrics_content_type(accept))


if __name__ == "__main__":
    unittest.main()
