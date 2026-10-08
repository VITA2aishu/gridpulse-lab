import unittest
from datetime import datetime, timezone
from silence_monitor import SilenceMonitor


class SilenceTests(unittest.TestCase):
    def setUp(self):
        self.monitor = SilenceMonitor(0)
        self.receipt = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
        self.event = dict(source_id='demo-a', event_time=self.receipt.isoformat(), value=1)

    def test_initial_grace_boundary_and_no_repeat(self):
        self.assertEqual(self.monitor.poll(59.9), [])
        records = self.monitor.poll(60)
        self.assertEqual(len(records), 2)
        self.assertTrue(all(r['reason'] == 'no_initial_fresh_arrival' for r in records))
        self.assertEqual(self.monitor.poll(61), [])

    def test_invalid_late_future_do_not_recover(self):
        self.monitor.poll(60)
        for event in (dict(self.event, value='bad'),
                      dict(self.event, event_time='2026-10-07T11:58:00Z'),
                      dict(self.event, event_time='2026-10-07T12:01:00Z')):
            self.assertEqual(self.monitor.observe(event, self.receipt, 61), [])
        self.assertIn('demo-a', self.monitor.missing)
        recovered = self.monitor.observe(self.event, self.receipt, 62)
        self.assertEqual(recovered[0]['status'], 'recovered')
        self.assertEqual(self.monitor.observe(self.event, self.receipt, 63), [])
        self.assertEqual(self.monitor.poll(122), [])
        self.assertEqual(self.monitor.poll(123)[0]['source_id'], 'demo-a')

    def test_sources_independent(self):
        self.monitor.observe(self.event, self.receipt, 30)
        self.assertEqual(self.monitor.poll(60)[0]['source_id'], 'demo-b')
        self.assertEqual(self.monitor.poll(90)[0]['reason'], 'no_fresh_arrival')

    def test_clock_and_configuration_validation(self):
        for timeout in (0, -1, True, float('inf')):
            with self.assertRaises(ValueError):
                SilenceMonitor(0, timeout)
        self.monitor.poll(10)
        with self.assertRaises(ValueError):
            self.monitor.poll(9)
        with self.assertRaises(ValueError):
            self.monitor.poll(float('nan'))


if __name__ == '__main__':
    unittest.main()
