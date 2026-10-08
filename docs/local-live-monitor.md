# Monitor usable-arrival silence in real time

This local-only runner connects the tested HTTP receiver to the silence monitor. No cloud account or external Python package is needed. It binds to 127.0.0.1 and has no authentication; use only synthetic data on your local machine.

## Windows walkthrough

Download the latest repository ZIP, extract it and open PowerShell in the folder containing README.md. Stop any earlier receiver with Ctrl+C to free port 8080.

```powershell
py -3.13 -m unittest discover -s examples/google-cloud -p "test_*.py" -v
py -3.13 examples/google-cloud/local_monitored_receiver.py --timeout 10
```

Expected: 17 tests pass. Leave the receiver running. After about 10–11 seconds, demo-a and demo-b each log missing with WARNING. An outage is logged once, not every second.

In a second PowerShell window, paste the entire block:

```powershell
$reading = @{
    source_id = "demo-a"
    event_time = [DateTimeOffset]::UtcNow.ToString("o")
    value = 12.5
}
Invoke-RestMethod -Uri "http://127.0.0.1:8080/telemetry" -Method Post -ContentType "application/json" -Body ($reading | ConvertTo-Json)
```

The response should be fresh. The receiver window logs recovered with INFO for demo-a, plus its arrival classification. demo-b stays missing. Stop sending; about 10–11 seconds after the accepted fresh reading, demo-a logs missing again. To recover again, refresh event_time before resending.

The 10-second timeout is for this walkthrough. Default timeout is 60 seconds. Late, invalid and future readings do not reset the silence timer. Healthz continues to report process_only even during missing-data conditions.

Stop the runner with Ctrl+C. Its polling thread stops with it.

## Design and limits

The watcher polls once per second, independently of incoming HTTP requests. A lock serializes clock sampling and monitor updates between the watcher and request handling. Timers use time.monotonic; UTC timestamps in logs describe observation time. Only fresh classified arrivals reset a source timer. This detects missing usable arrivals, including streams that only send unusable readings; it does not identify the root cause.

The WSGI development server is single-process and not production hardened. Monitor state resets on restart. No durable state, distributed coordination, external notifications, frozen-value detection or authentication is provided. Slow clients can block the HTTP development server although the watcher continues polling. Run this teaching example only on localhost.

The original receiver.py command and container entry point remain arrival-only. The new local runner has not been deployed to Cloud Run; in-process background polling is not a reliable cloud silence detector when instances scale down or restart.

Validation: all 17 tests passed locally, including real HTTP recovery, source independence, missing transition, background polling and shutdown. User-run Windows verification of the earlier 15-test simulated example also passed; this new 17-test version still requires user-side verification.
