# Validate a Cloud Run log alert through email delivery

A late-event warning is useful only if an operator receives it. This lab tests
that path in two stages: a manually written log to check the notification
configuration, then an authenticated request to the deployed telemetry receiver.
All events use fictional `demo-a` data. This is a learning experiment, not a
production monitoring deployment.

## Results verified on October 8, 2026

| Check | Observed result | Evidence |
|---|---|---|
| Receiver tests before deployment | 6 tests passed | Cloud Shell output |
| Manually written matching log | WARNING, late, synthetic_test=true | Exported JSON |
| Manual-log notification | Incident opened; email received for Global resource | Incident and email screenshots |
| Authenticated receiver POST | HTTP 200; late; age 121.452976 seconds | Saved request and response JSON |
| Receiver application log | WARNING; event_age_exceeded; Cloud Run revision | Exported JSON |
| Application-log notification | Incident opened; email received for matching revision | Incident and email screenshots |
| Cleanup | Zero services, repositories, buckets, policies and channels; lab accounts deleted | Cloud Shell resource lists |

The application run used revision `telemetry-receiver-00001-bkk` in
`us-central1`. Its application log has request ID
`49859731-f5d4-490d-ba0c-a0f688eb5f27` and timestamp
`2026-10-08T21:14:16.159569Z`. The email identifies that same revision.
No precise notification-latency measurement was taken.

The retained evidence archive contains six JSON files: manual log, application
request/response, application log, policy creation configuration, service
configuration and service IAM policy. Incident, email and cleanup screenshots
were retained separately. The policy file is the creation input, not an API
export of the resulting policy. Raw exports remain private because service
configuration can contain account identities and project identifiers.

## 1. Deploy the private receiver

Follow [the secure receiver guide](google-cloud-secure-receiver.md) for source,
prerequisites, deployment and IAM testing. Use a billing-enabled disposable
project, separate build and runtime accounts, and IAM-authenticated invocation.
This alerting run used new `telemetry-alert-build` and
`telemetry-alert-runtime` accounts after the earlier lab was cleaned up.
The build account received `roles/run.builder`; no project role was granted to
the runtime account. Source deployment created a container repository and source
bucket. The service used minimum zero and maximum one instance.

The test caller in this run was the signed-in project operator using a user ID
token. Dedicated service-account caller permissions were tested separately in
[the access-control experiment](cloud-run-access-control-lessons.md).

## 2. Create the email channel and policy

Enable the Logging and Monitoring APIs. In Monitoring, create an email
notification channel using an address you control. Save its full resource name.
Create a log-based alert with this filter:

```text
severity=WARNING
AND jsonPayload.component="telemetry_receiver"
AND jsonPayload.status="late"
AND (
  log_id("gde-alert-validation")
  OR (
    resource.type="cloud_run_revision"
    AND resource.labels.service_name="telemetry-receiver"
  )
)
```

Use one `conditionMatchedLog` condition, combiner `OR`, the email channel,
`notificationRateLimit.period` of `300s`, and `autoClose` of `1800s`.
The validated policy was named **GDE Lab - Late Telemetry**, with condition
**Late telemetry warning**. Its documentation told readers to distinguish
manual synthetic tests from application results. The receiver also uses generated
test telemetry; neither stage represents a real operational incident.

The filter deliberately admits the manual validation log. For an application-only
policy, remove that branch and retain the Cloud Run resource and service filters.
No policy severity was set in this experiment. The email's **No severity** label
therefore does not contradict the matched log's **WARNING** severity.

## 3. Check notification wiring with one manual log

In Cloud Shell, substitute your project ID:

```bash
gcloud logging write gde-alert-validation \
  '{"component":"telemetry_receiver","status":"late","reason":"event_age_exceeded","source_id":"demo-a","synthetic_test":true,"test_id":"gde-alert-test-001","message":"Synthetic test of Logging to email notification"}' \
  --payload-type=json --severity=WARNING --project=YOUR_PROJECT_ID
```

Check the log, opened incident and received email. This stage validates the
Logging-to-notification path. It does not execute the receiver. The default
resource for this manually written entry was Global.

## 4. Execute the application path

Run this in Cloud Shell after deployment, replacing the project ID:

```bash
python3 - <<'PY'
import datetime
import json
import subprocess
import urllib.request

url = subprocess.check_output([
    "gcloud", "run", "services", "describe", "telemetry-receiver",
    "--project=YOUR_PROJECT_ID", "--region=us-central1",
    "--format=value(status.url)"
], text=True).strip()
token = subprocess.check_output(
    ["gcloud", "auth", "print-identity-token"], text=True
).strip()
event = {
    "source_id": "demo-a",
    "event_time": (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.timedelta(seconds=120)).isoformat(),
    "value": 42.0,
}
request = urllib.request.Request(
    url + "/telemetry", data=json.dumps(event).encode(),
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(request, timeout=60) as response:
    print("HTTP", response.status)
    print(response.read().decode())
PY
```

The receiver should classify the event as late. Save its response and find the
corresponding structured application log. Confirm the incident and email carry
the same service/revision labels. Do not infer delivery from HTTP 200 alone.
Avoid repeated sends while investigating; notification rate limits affect repeats.

## What this detects and what it misses

This policy detects an **arriving event classified as late**. A source that stops
sending entirely produces no matching event, so this policy does not detect
silence. Missing-data detection needs a separate design; see the
[local missing-data experiment](local-missing-data.md) for the underlying concept.
Its local process watchdog should not be transplanted into a Cloud Run service
that scales to zero or uses multiple instances.

Automatic incident closure is not proof that telemetry recovered. This lab did
not validate recovery notifications, repeated-alert behavior, counts, missing-data
alerts, load handling or production reliability. Matching-log alerts also differ
from metric thresholds: use log-based metrics when the question is a count or rate.

## Preserve evidence, then clean up

Before deletion, export the response, logs, policy input, service configuration
and service IAM policy; save incident and email screenshots. Keep credentials
out of all exports. Delete the service, lab container repository and source
bucket; remove the build-role binding and lab accounts; delete the alert policy
before its notification channel. Only delete resources created for this lab.

List services, repositories across all locations, buckets, policies, channels
and service accounts afterward. This run confirmed zero lab resources in those
lists; the default Compute Engine account remained. Cleanup does not establish
a zero bill: completed usage and retained/soft-deleted storage can still affect
billing. Final costs were not measured in this experiment.

## Reproduce and report

If you try this lab, report the source commit, region, HTTP classification,
matching resource labels, whether the incident opened and whether email arrived.
Include failures and useful corrections in a repository issue. Remove tokens,
email addresses and private identifiers before sharing screenshots. Independent
reproductions are welcome; none are claimed by this validation report.

## Official references

- [Configure log-based alerting policies](https://docs.cloud.google.com/logging/docs/alerting/log-based-alerts)
- [Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [Cloud Run logging](https://docs.cloud.google.com/run/docs/logging)
