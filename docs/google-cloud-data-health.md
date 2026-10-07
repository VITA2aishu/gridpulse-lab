# Your service is healthy, but is your data fresh?

By Aisvarya Sampath Kumar · 7 October 2026

A receiver can return successful responses while accepting old or invalid readings. An availability check alone cannot tell you whether the data is useful. This tutorial separates service availability from the quality of individual telemetry arrivals, using a dependency-free Python example and a Google Cloud logging design.

**Validation status:** the example and its tests have been run locally. The Cloud Run integration described here has not been deployed or tested in a Google Cloud project. No production performance or adoption results are claimed.

## Start with two timestamps

Keep the original event timestamp and the receiver's timestamp. Their difference gives event age at reception. A delayed reading can arrive through a healthy service, so measure this separately from request latency. Clock skew can also affect the difference: a future timestamp needs investigation rather than being silently treated as fresh.

The example uses two fictional source identifiers. It rejects nonnumeric and nonfinite values, requires timezone-aware timestamps, and classifies accepted timestamps against a 60-second age limit and a five-second future tolerance. These are demonstration thresholds, not universal operational settings.

## Run the example

From a checkout of this repository, use Python 3.11 or newer:

```text
python examples/google-cloud/telemetry_logs.py
python -m unittest discover -s examples/google-cloud -p "test_telemetry_logs.py" -v
```

These commands work without shell-specific environment-variable syntax, cloud credentials or third-party packages. The script prints four JSON lines in this order: `fresh`, `late`, `invalid`, `future`. Because timestamps are fixed, results are deterministic. They are synthetic fixtures, not current readings.

The tests cover the scenario classifications, threshold boundaries, timezone equivalence, malformed timestamps, invalid numeric values and invalid configuration. The example does not maintain stream state or deduplicate deliveries.

## Send the same shape of logs from Cloud Run

Cloud Run captures container output. Emit each record as one serialized JSON line to standard output. Cloud Logging parses structured JSON into `jsonPayload`; a `severity` field supplies the log severity. This approach does not require adding the Cloud Logging client library just to print these records. See [Cloud Run logging](https://docs.cloud.google.com/run/docs/logging).

In an actual receiver, replace the fixed demonstration timestamp with a timezone-aware receipt timestamp and call `classify` for each decoded reading. Keep receipt time consistent throughout processing. Validate transport envelopes separately. This example is not an HTTP server or a Pub/Sub subscriber.

After integrating it into a Cloud Run service, a Logs Explorer filter for late readings would be:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="YOUR_SERVICE_NAME"
jsonPayload.component="telemetry_demo"
jsonPayload.status="late"
```

Replace the service name with the actual deployed service. Keep identifiers bounded if you later extract metric labels; per-message IDs and event timestamps are poor metric-label choices. Logs can retain detailed context while metrics summarize behavior.

## An arrival check cannot detect silence

If no reading arrives, this classifier never runs. Detecting source silence requires a separate signal: for example, an external scheduled check of durable last-valid-event state. That state must survive restarts and be shared across service instances. Decide explicitly whether an invalid or old reading should advance last-valid state; normally it should not.

Another option is a Cloud Monitoring metric-absence policy on an appropriate established series. Verify that the policy has observed data, uses the intended resource and labels, and matches the expected sampling interval. Absence is different from a reported zero. Read Google's [metric-absence policy guidance](https://docs.cloud.google.com/monitoring/alerts/metric-absence) before choosing it; a never-established series needs special consideration.

An arrival carrying an old event and a source that sends nothing are different failure modes. A third mode is an unchanged value arriving with new timestamps. Detecting that requires progression checks and domain context: a stable value can be valid.

## Extend the lab carefully

Useful next steps are a real receiver, explicit delivery-retry behavior, durable state, and a controlled source-stop exercise. Measure actual alert delay after those pieces run. Compare data-quality alerts with service-error alerts so a developer can see which layer failed.

This first example deliberately demonstrates only arrival classification and structured output. It gives readers a small, reproducible starting point for data-health instrumentation before adding cloud infrastructure or AI explanations.
