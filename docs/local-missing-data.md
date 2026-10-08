# Detect missing telemetry locally

A healthy process does not mean usable readings are arriving. This standalone Python demo tracks two synthetic sources, demo-a and demo-b, without a cloud account or additional packages. It supplements the arrival-quality receiver; it is not wired into the HTTP server.

## Run on Windows

Download the latest repository ZIP and extract it. Open PowerShell in the extracted repository root (the folder containing README.md).

```powershell
py -3.13 -m unittest discover -s examples/google-cloud -p "test_*.py" -v
py -3.13 examples/google-cloud/silence_monitor.py
```

Expected: 15 passing tests, then three JSON log lines. demo-a becomes missing after 60 seconds without a fresh arrival; demo-b becomes missing because no initial reading arrived. demo-a then recovers. The demo uses a simulated elapsed clock, so it completes immediately rather than waiting 92 seconds.

## Policy

- Both expected sources receive a 60-second startup grace period.
- At or beyond 60 seconds since the last fresh arrival, poll emits a WARNING once per outage.
- Invalid, late, and future readings do not reset the timer.
- A fresh reading resets the timer and emits INFO recovery if that source was missing.
- Each source has its own timer. Recovery of one does not recover the other.
- No raw payloads or credentials are logged.

The monitor takes elapsed clock values from its caller. A live caller should use time.monotonic(), call observe for arrivals, and poll periodically even when no arrivals occur. Detection latency depends on polling frequency. Event timestamps are used for arrival quality, not the silence timer. This policy tracks usable-arrival silence; it does not distinguish network silence from a stream of unusable readings.

## Limits

State is in memory and resets on restart. There is no background scheduler, persistence, multi-process coordination, notification delivery, or Cloud Logging integration. The HTTP receiver and monitor are separate. This is a tested teaching example, not a deployed monitoring service. It does not detect frozen event timestamps, duplicates, or stream progression within the freshness window.

Validated locally with all 15 unit/integration tests, including the existing receiver HTTP roundtrip. Cloud deployment remains unverified.
