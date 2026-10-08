# Build an observable telemetry receiver with restricted Cloud Run access

By Aisvarya Sampath Kumar · 7 October 2026

This follow-up to the [data-health tutorial](google-cloud-data-health.md) adds a real HTTP receiver. It demonstrates the Security and Operations intersection: explicit request validation, bounded structured logs, process readiness, and a proposed Cloud Run deployment that requires authenticated callers.

**Verified locally:** all 11 tests pass, including a real HTTP request. **Not yet verified:** Docker image build, Gunicorn startup, Google Cloud deployment, IAM enforcement, audit-log behavior, Cloud Monitoring metrics, alerts or cloud costs. This is a small learning example, not a production-ready telemetry platform.

## Local walkthrough — no Google Cloud account needed

Use Python 3.11+ from the repository root:

```text
python -m unittest discover -s examples/google-cloud -p "test_*.py" -v
python examples/google-cloud/receiver.py
```

The development server binds only to `127.0.0.1:8080`. In a second PowerShell window:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/health"
$reading = @{source_id="demo-a"; event_time=[DateTimeOffset]::UtcNow.ToString("o"); value=12.5}
Invoke-RestMethod -Uri "http://127.0.0.1:8080/telemetry" -Method Post -ContentType "application/json" -Body ($reading | ConvertTo-Json)
```

Expect `ready` with `checks: process_only` from health, and `fresh` from telemetry. To exercise a late reading, replace the event timestamp with `[DateTimeOffset]::UtcNow.AddMinutes(-2).ToString("o")`. To exercise a future timestamp, use `AddSeconds(30)`. For an invalid value, use `value="bad"`; this returns HTTP 422 and PowerShell reports an HTTP error. Check the server's JSON log line to see `invalid_value`.

The automated tests exercise the same behavior without PowerShell or external packages. Stop the development server with Ctrl+C.

Cloud Run reserves some URL paths ending in `z`. This example uses `/health` to avoid that restriction; see [known issues](https://docs.cloud.google.com/run/docs/known-issues#reserved-url-paths).

## Request contract

| Endpoint or condition | Result |
| --- | --- |
| `GET /health` | 200, process readiness only |
| `POST /telemetry`, valid fresh/late/future reading | 200 with quality classification |
| Invalid reading value/source/timestamp | 422, or 400 for schema/length errors |
| Malformed JSON, duplicate fields, nonstandard JSON numbers | 400 |
| Body larger than 4,096 bytes | 413 |
| Media type other than `application/json` | 415 |
| Missing or malformed Content-Length | 411 |
| Wrong method on an existing endpoint | 405 |

The exact JSON fields are `source_id`, `event_time`, and `value`. Only fictional sources `demo-a` and `demo-b` are accepted. Unknown fields are rejected. A late reading still receives 200 because classification completed successfully; downstream consumers must inspect `status`. This does not imply successful storage.

## Security choices and their boundaries

The application logs classifications and bounded rejection reasons. It does not log raw bodies, authorization headers or query strings. The tests check that a synthetic secret does not leak through the application response or logs. Platform request logs are separate and may contain URLs, so never put credentials in URLs.

The local server has no authentication and is restricted to loopback. In the proposed deployment, **Cloud Run IAM handles authentication before the request reaches this application**. The Python code does not validate ID tokens. Do not expose the local development server publicly or deploy this example with public invocation enabled.

The Dockerfile uses a non-root user and copies only the receiver, classifier and server configuration. The scoped `.dockerignore` keeps other files out of the build context. Gunicorn listens on the Cloud Run `PORT` value through its configuration; the standard-library server is used only for local development. Dependency constraints permit compatible updates; pin the resolved dependencies and base-image digest after testing an actual build.

## Proposed cloud deployment — run after account and cost setup

Use a new dedicated demo service. Before deployment, choose a personal project, region and spending limit. Enable the required Cloud Run, Cloud Build and Artifact Registry APIs and configure deployment permissions using Google's current guidance. Build/deployer permissions are distinct from runtime permissions. This guide does not grant project-wide Owner or Editor access.

Create a dedicated user-managed runtime service account. The current receiver calls no Google Cloud APIs, so it needs no application-specific Google API roles. If storage or direct API calls are added later, grant only the required resource permissions. Do not download a service-account key.

With those prerequisites ready, this single-line command uses the example folder as the source build context:

```text
gcloud run deploy telemetry-receiver --source examples/google-cloud --project YOUR_PROJECT_ID --region YOUR_REGION --service-account YOUR_RUNTIME_SERVICE_ACCOUNT_EMAIL --no-allow-unauthenticated --invoker-iam-check --min 0 --max 1 --concurrency 4 --timeout 15 --memory 256Mi --cpu 1
```

Replace every `YOUR_...` placeholder. This is a documented deployment recipe, not an executed deployment. Scaling limits reduce exposure to resource usage but are not a hard spending cap; builds, image storage and logs can also incur costs.

Grant `roles/run.invoker` on this service only to the intended test user. Authentication-required access can still use an internet-reachable URL; this configuration does not create private network ingress. Check that neither `allUsers` nor `allAuthenticatedUsers` has invocation access.

Verify the deployed service, rather than assuming the command guarantees its policy:

```text
gcloud run services get-iam-policy telemetry-receiver --project YOUR_PROJECT_ID --region YOUR_REGION
gcloud run services describe telemetry-receiver --project YOUR_PROJECT_ID --region YOUR_REGION --format export
```

Confirm the runtime identity, enabled invoker check, traffic settings and absence of broad invocation grants. Test `/health` without credentials: it should fail at the platform layer. Then test with a permitted identity. For a development-only PowerShell request:

```powershell
$serviceUrl = "YOUR_DEPLOYED_SERVICE_URL"
$idToken = gcloud auth print-identity-token
Invoke-RestMethod -Uri "$serviceUrl/health" -Headers @{Authorization="Bearer $idToken"}
Remove-Variable idToken
```

Never print or publish the token. Repeat the telemetry scenarios with the same authorization header. Record actual response codes and logs after execution. Developer CLI tokens are for testing; production service-to-service calls need the appropriate audience-bound identity token.

## Observe classifications

Use this Logs Explorer filter after a real deployment:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="telemetry-receiver"
jsonPayload.component="telemetry_receiver"
```

Add `jsonPayload.status="late"` to inspect old arrivals. Use the generated request ID to connect an application response to its classification log. Cloud Logging handles JSON output; no Logging API client is required for the example's stdout logs.

Separately review Cloud Run administrative audit logs for deployment and IAM changes. Do not assume every invocation appears as a Data Access audit entry; confirm enabled audit settings and actual behavior in the test project. Retain only redacted evidence.

## What this example does not cover

There is no persistence, source-silence detector, duplicate suppression, Pub/Sub envelope handling, rate limiter or alert policy. HTTP success means the reading was evaluated, not stored durably. A process readiness check cannot prove data freshness. Future work should add durable last-valid-event state and an independent scheduled checker before claiming missing-data detection. Authentication also does not make an authorized caller's data trustworthy; input validation remains necessary.

After testing, remove the demo service and review any build images, runtime service account and separately created monitoring resources for cleanup. Keep a record of actual runs before publishing cloud-result claims.

## Official references checked 7 October 2026

- [Cloud Run developer authentication](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [Service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)
- [Container port configuration](https://docs.cloud.google.com/run/docs/configuring/services/containers)
- [Deployment command reference](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)
- [Cloud Run structured logging](https://docs.cloud.google.com/run/docs/logging)
