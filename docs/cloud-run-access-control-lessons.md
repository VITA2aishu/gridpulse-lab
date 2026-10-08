# Testing Cloud Run access controls with a telemetry receiver

By Aisvarya Sampath Kumar · 7 October 2026

A successful deployment answers one question: can the service run? It leaves other questions open. Can an unexpected caller reach it? Can an intended caller reach it with a narrowly scoped grant? Can operators distinguish a healthy process from unhealthy data?

This lab uses a small Python telemetry receiver to examine those questions on Google Cloud. The code, tests and [deployment walkthrough](google-cloud-secure-receiver.md) are public. The receiver uses fictional data and does not connect to production systems.

## Start with two separate health questions

The receiver exposes `GET /health` and `POST /telemetry`. The first reports process readiness. The second validates and classifies an incoming reading.

A service can return a healthy response while accepting data that is two minutes old. That is why the health response explicitly says `checks: process_only`. It makes no promise about a continuously arriving stream.

Each reading has three fields:

```json
{"source_id":"demo-a","event_time":"2026-10-08T02:24:23Z","value":12.5}
```

Generate a current timestamp when reproducing the fresh case; the fixed timestamp above illustrates the schema. The example accepts only fictional sources `demo-a` and `demo-b`. It rejects unknown fields, invalid timestamps and invalid numeric values. It also bounds request bodies and rejects duplicate JSON keys.

The classifier compares event time with arrival time. An age greater than 60 seconds is late. A timestamp more than five seconds ahead of arrival is future. These thresholds are teaching defaults, not universal operational requirements.

## Separate the identities

Three service accounts were used for different responsibilities:

| Identity | Responsibility | Lab permission choice |
| --- | --- | --- |
| Build account | Build the source deployment | Cloud Run Builder role |
| Runtime account | Run the receiver | No direct project roles; the app makes no Google API calls |
| Caller account | Invoke the deployed service | Cloud Run Invoker on this service after the negative test |

The build account's capabilities do not belong to the runtime account simply because both participate in deployment. Likewise, permission to create an identity token is separate from permission to invoke the service.

The project used for this exercise had an existing default compute service account with Editor. The receiver did not run as that identity. Separating these accounts improved the application's permission boundaries, but it did not establish least privilege for the entire project.

## Test denial before granting access

Testing with a project owner is a useful smoke test. It does not isolate a service-scoped caller grant because the owner already has broad permissions.

The more informative sequence used the dedicated caller account:

1. Create an audience-bound ID token for the caller.
2. Invoke `/health` before adding its service invocation binding.
3. Add `roles/run.invoker` on the receiver service.
4. Invoke the same endpoint as the same caller again.

The first request returned HTTP 403. The later request returned HTTP 200 with process readiness. An unauthenticated request also returned 403.

These results provide evidence for the tested caller and service configuration. They do not prove that every other principal lacks access. Inspect service and inherited project policies as well as authentication settings.

The service retained an internet-reachable URL with IAM authentication required. This exercise did not configure private network ingress.

## Avoid widening permissions just to satisfy a command

The operator received `roles/iam.serviceAccountOpenIdTokenCreator` on the caller account. In this lab, the attempted impersonating gcloud command requested access-token permissions and failed before it could invoke the service.

Rather than add the broader Service Account Token Creator role, the test called IAM Credentials `generateIdToken` directly. The request supplied the deployed service URL as the audience and requested the service-account email claim. Tokens stayed in memory and were not published.

This distinction matters when diagnosing a failure: inability to mint a token and inability to invoke Cloud Run are different stages. A token-creation error is not evidence that Cloud Run denied the caller.

For reproduction in Cloud Shell, enable the IAM Service Account Credentials API, grant the operator the narrow token role on the caller account, and set these variables to your own lab resources:

```bash
export LAB_PROJECT="YOUR_PROJECT_ID"
export LAB_REGION="YOUR_REGION"
export LAB_CALLER="telemetry-caller@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

The operator must already be signed in to gcloud and permitted to describe the service. Run this script before and after the invocation grant:

```python
import json
import os
import subprocess
import urllib.error
import urllib.request

project = os.environ["LAB_PROJECT"]
region = os.environ["LAB_REGION"]
caller = os.environ["LAB_CALLER"]
url = subprocess.check_output([
    "gcloud", "run", "services", "describe", "telemetry-receiver",
    "--project", project, "--region", region,
    "--format=value(status.url)",
], text=True).strip()
access_token = subprocess.check_output(
    ["gcloud", "auth", "print-access-token"], text=True
).strip()

endpoint = (
    "https://iamcredentials.googleapis.com/v1/projects/-/"
    "serviceAccounts/" + caller + ":generateIdToken"
)
request = urllib.request.Request(
    endpoint,
    data=json.dumps({"audience": url, "includeEmail": True}).encode(),
    headers={
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(request) as response:
        token = json.load(response)["token"]
except urllib.error.HTTPError as error:
    print("Token creation failed:", error.code)
    raise SystemExit(1)

request = urllib.request.Request(
    url + "/health", headers={"Authorization": "Bearer " + token}
)
try:
    with urllib.request.urlopen(request) as response:
        print("Invocation HTTP", response.status)
        print(response.read().decode())
except urllib.error.HTTPError as error:
    print("Invocation HTTP", error.code)
```

Save it as a local script and run it with Python 3. This version reports the invocation status without printing credentials. Between runs, grant invocation:

```bash
gcloud run services add-iam-policy-binding telemetry-receiver \
  --project="$LAB_PROJECT" --region="$LAB_REGION" \
  --member="serviceAccount:$LAB_CALLER" \
  --role=roles/run.invoker --condition=None
```

## Inspect data quality independently of HTTP success

The cloud run produced these outcomes:

| Input | HTTP response | Application classification log |
| --- | --- | --- |
| Current valid reading | 200 | INFO, fresh |
| Reading about 120 seconds old | 200 | WARNING, late, event_age_exceeded |
| Reading about 30 seconds ahead | 200 | WARNING, future, clock_or_timestamp_error |
| Invalid value | 422 | WARNING, invalid, invalid_value |

Late and future readings receive HTTP 200 because the classification completed. The response does not claim that the data is fresh or stored durably. Consumers must inspect the classification.

Application logs contain bounded reasons and generated request IDs. They do not contain raw request bodies or authorization headers. Platform request logs are separate, so credentials should never be placed in URLs.

Use this Logs Explorer filter:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="telemetry-receiver"
jsonPayload.component="telemetry_receiver"
```

Filter by the returned request ID to locate an individual classification. A matching fresh INFO record and all three WARNING scenarios were inspected in the lab.

## Check the administrative audit trail

The service IAM change appeared in Cloud Run Admin Activity logs as `google.cloud.run.v1.Services.SetIamPolicy`. The record's request policy included the dedicated caller and `roles/run.invoker`.

```bash
gcloud logging read \
  'log_id("cloudaudit.googleapis.com/activity") AND protoPayload.serviceName="run.googleapis.com" AND protoPayload.methodName:"SetIamPolicy"' \
  --project="$LAB_PROJECT" --freshness=1h --limit=5 \
  --format='json(timestamp,protoPayload.resourceName,protoPayload.request.policy)'
```

The observed binding record was timestamped `2026-10-08T02:36:54.382332Z`. The policy content and the before/after request outcomes complement each other: one records the administrative request, while the other tests behavior.

This exercise did not verify Data Access audit logging for invocations. Application classification logs, platform request logs and administrative audit logs answer different questions.

## A health-route problem discovered during deployment

The initial implementation used `/healthz`. Cloud Run returned a platform HTML 404 on the deployed route. Changing the application and tests to `/health`, then redeploying, produced the expected authenticated readiness response.

Google documents reservations affecting some paths ending in `z` and recommends avoiding that suffix. The observed behavior was consistent with this restriction. A locally working route should still be checked through the deployed platform.

## Reproduce and extend the lab

From the repository root, run:

```bash
python -m unittest discover -s examples/google-cloud -p "test_*.py" -v
```

All 17 example tests passed during validation. Follow the [receiver walkthrough](google-cloud-secure-receiver.md) for local requests, deployment settings and additional boundaries.

The cloud receiver does not persist readings, suppress duplicates, detect frozen values or detect source silence. The repository has separate local missing-data examples; those should not be treated as a durable distributed monitor for Cloud Run. A process that scales to zero cannot supply a dependable always-running in-memory watchdog.

Further work should evaluate durable last-valid-event state, an independent scheduled checker and tested alert delivery. Cloud Monitoring metrics, alert delivery, final charges and Data Access audit behavior remain unverified here.

After recording results, review the lab service, build images and service accounts for cleanup. The tested configuration used minimum scale zero and service-level maximum scale one, but scaling settings do not bound all project charges.

If you reproduce the exercise, an issue with the environment, exact command, response status and redacted logs is useful feedback. Do not include credentials or production telemetry. The goal is to make both successful runs and limitations understandable to the next developer.

## Official references

- [Cloud Run developer authentication](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [Cloud Run service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)
- [Cloud Run custom build service accounts](https://docs.cloud.google.com/run/docs/configuring/services/build-service-account)
- [Create short-lived service account credentials](https://docs.cloud.google.com/iam/docs/create-short-lived-credentials-direct)
- [Cloud Run logging](https://docs.cloud.google.com/run/docs/logging)
- [Cloud Run known issues](https://docs.cloud.google.com/run/docs/known-issues)
