import io
import json
import threading
import unittest
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server
from local_monitored_receiver import MonitoredReceiver
from receiver import QuietHandler


class MonitoredTests(unittest.TestCase):
    def test_http_missing_invalid_and_recovery(self):
        now = [0]
        logs = []
        app = MonitoredReceiver(timeout=10, clock=lambda: now[0], sink=logs.append)
        with make_server('127.0.0.1', 0, app, handler_class=QuietHandler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                root = 'http://127.0.0.1:' + str(server.server_port)
                now[0] = 10
                app.poll()
                self.assertEqual(len(logs), 2)
                event = dict(source_id='demo-a', event_time=datetime.now(timezone.utc).isoformat(), value=12.5)
                response = urlopen(Request(root+'/telemetry', data=json.dumps(event).encode(), headers={'Content-Type':'application/json'}))
                self.assertEqual(json.load(response)['status'], 'fresh')
                self.assertEqual(logs[-1]['status'], 'recovered')
                self.assertIn('demo-b', app.monitor.missing)
                now[0] = 20
                app.poll()
                self.assertEqual(logs[-1]['status'], 'missing')
                app.observe(dict(event, value='bad'), datetime.now(timezone.utc))
                self.assertIn('demo-a', app.monitor.missing)
                with urlopen(root+'/health') as response:
                    self.assertEqual(json.load(response)['checks'], 'process_only')
            finally:
                server.shutdown()
                thread.join()

    def test_background_polling_and_stop(self):
        logs = []
        alerted = threading.Event()
        def sink(record):
            logs.append(record)
            alerted.set()
        app = MonitoredReceiver(timeout=0.02, sink=sink)
        stop = threading.Event()
        thread = threading.Thread(target=app.watch, args=(stop, 0.005))
        thread.start()
        try:
            self.assertTrue(alerted.wait(2))
        finally:
            stop.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(logs), 2)
