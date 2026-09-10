import unittest

from gridpulse.metrics import _sample


class MetricsTests(unittest.TestCase):
    def test_sample_escapes_prometheus_label_values(self):
        """Prometheus labels must not let quotes, slashes, or newlines break a sample."""
        value = 'fictional "asset"\\line\nwest'

        self.assertEqual(
            'gridpulse_test{asset_id="fictional \\"asset\\"\\\\line\\nwest"} 1',
            _sample("gridpulse_test", 1, asset_id=value),
        )


if __name__ == "__main__":
    unittest.main()
