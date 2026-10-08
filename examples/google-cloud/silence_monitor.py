"""Local, in-memory watchdog demo; no Google Cloud account required."""
import json
import math
from telemetry_logs import classify
from datetime import datetime, timezone


class SilenceMonitor:
    """Track usable arrivals using elapsed monotonic seconds, not event clocks."""
    def __init__(self, started_at, timeout=60):
        self._number(started_at)
        self._number(timeout)
        if timeout <= 0:
            raise ValueError('timeout must be positive')
        self.timeout = timeout
        self.last = dict.fromkeys(('demo-a', 'demo-b'), started_at)
        self.seen = set()
        self.missing = set()
        self.clock = started_at

    @staticmethod
    def _number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('clock and timeout must be finite numbers')

    def _advance(self, now):
        self._number(now)
        if now < self.clock:
            raise ValueError('elapsed clock must not move backwards')
        self.clock = now

    def observe(self, event, received_at, now):
        self._advance(now)
        record = classify(event, received_at)
        if record['status'] != 'fresh':
            return []
        source = record['source_id']
        self.last[source] = now
        self.seen.add(source)
        if source in self.missing:
            self.missing.remove(source)
            return [self._record(source, 'recovered', 'fresh_arrival_resumed', 0)]
        return []

    def poll(self, now):
        self._advance(now)
        records = []
        for source, last in self.last.items():
            age = now - last
            if age >= self.timeout and source not in self.missing:
                self.missing.add(source)
                reason = 'no_fresh_arrival' if source in self.seen else 'no_initial_fresh_arrival'
                records.append(self._record(source, 'missing', reason, age))
        return records

    @staticmethod
    def _record(source, status, reason, age):
        return dict(component='local_silence_monitor', source_id=source,
                    status=status, reason=reason, silence_seconds=age,
                    severity='WARNING' if status == 'missing' else 'INFO')


def demo_records():
    monitor = SilenceMonitor(0, timeout=60)
    receipt = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    event = dict(source_id='demo-a', event_time=receipt.isoformat(), value=12.5)
    monitor.observe(event, receipt, 0)
    yield from monitor.poll(60)
    yield from monitor.poll(90)  # No repeated alert during the same outage.
    yield from monitor.observe(dict(event, value='bad'), receipt, 91)
    yield from monitor.observe(event, receipt, 92)


if __name__ == '__main__':
    for record in demo_records():
        print(json.dumps(record, allow_nan=False), flush=True)
