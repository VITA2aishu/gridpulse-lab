"""Single-process local receiver with real-time usable-arrival monitoring."""
import argparse
import threading
import time
from datetime import datetime, timezone
from wsgiref.simple_server import make_server

from receiver import application, emit, QuietHandler
from silence_monitor import SilenceMonitor


class MonitoredReceiver:
    def __init__(self, timeout=60, clock=time.monotonic, sink=emit):
        self.clock = clock
        self.sink = sink
        self.lock = threading.Lock()
        self.monitor = SilenceMonitor(clock(), timeout)

    def _emit(self, records):
        for record in records:
            record['observed_at'] = datetime.now(timezone.utc).isoformat()
            self.sink(record)

    def observe(self, event, received_at):
        with self.lock:
            self._emit(self.monitor.observe(event, received_at, self.clock()))

    def poll(self):
        with self.lock:
            self._emit(self.monitor.poll(self.clock()))

    def __call__(self, environ, start_response):
        return application(environ, start_response, observer=self.observe)

    def watch(self, stop, interval=1):
        while not stop.wait(interval):
            self.poll()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    app = MonitoredReceiver(args.timeout)
    stop = threading.Event()
    with make_server('127.0.0.1', args.port, app, handler_class=QuietHandler) as server:
        watcher = threading.Thread(target=app.watch, args=(stop,), daemon=True)
        watcher.start()
        emit(dict(severity='INFO', component='local_silence_monitor',
                  message='Local monitored receiver ready', port=args.port,
                  timeout_seconds=args.timeout, poll_interval_seconds=1))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            watcher.join()


if __name__ == '__main__':
    main()
