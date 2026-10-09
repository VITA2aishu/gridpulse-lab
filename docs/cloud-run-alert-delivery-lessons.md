# A warning in Cloud Logging is only the start: testing Cloud Run alert delivery

My telemetry receiver returned HTTP 200 for an event that was more than two minutes old. That was expected: the request was valid, but its data was late. The application wrote a structured WARNING log. The next question was whether that warning would reach an inbox.

I tested this with a small, IAM-authenticated Cloud Run receiver using generated telemetry. The experiment covered the request, classification log, Monitoring incident and email notification. It also exposed a boundary that is easy to overlook: an alert for an arriving late event does not detect a source that has stopped sending.

## Test the notification wiring before testing the application

I split validation into two stages.

First, I manually wrote a JSON log with WARNING severity, component `telemetry_receiver`, status `late` and `synthetic_test: true`. A log-based policy matched it, opened an incident and delivered an email.

That proved the Logging-to-email path worked. It did not prove that the receiver emitted the right log. The email identified a Global resource because the manual log used that resource type.

Second, I sent an authenticated POST to the deployed receiver with an event timestamp set 120 seconds in the past. The receiver returned HTTP 200 with status `late` and an event age of 121.452976 seconds. The difference from exactly 120 seconds reflects elapsed time before classification; it is not a measurement of alert delivery latency.

The application emitted a WARNING log with reason `event_age_exceeded`. This time the resource was a Cloud Run revision. Monitoring opened an incident, and the email carried the same service and revision labels.

Separating the tests helped distinguish a notification configuration problem from a problem in the application logging path.

## Match the meaning of the log

The application writes bounded structured fields rather than asking an alert to interpret arbitrary prose. The application branch of the filter was:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="telemetry-receiver"
severity=WARNING
jsonPayload.component="telemetry_receiver"
jsonPayload.status="late"
```

The experiment's full policy also admitted the manually written validation log through a separate branch. That branch was useful for the first test. An application-only policy should remove it.

The policy used a five-minute minimum notification interval and a 30-minute automatic closure setting. I did not measure repeated-notification behavior or validate recovery notifications. These settings should not be treated as evidence that either behavior was tested.

One visible detail was the email's “No severity” label. The policy did not set a policy severity, even though the matched application log had WARNING severity. Those are separate fields. When documenting the result, I kept both facts instead of interpreting the label as a missing warning.

## Correlate the response, log, incident and email

A successful HTTP response is not sufficient evidence of notification delivery. Each part of the path answers a different question:

| Evidence | What it established in this run |
|---|---|
| Saved HTTP response | The receiver accepted the request and classified it as late |
| Structured application log | The receiver emitted the expected warning and reason |
| Monitoring incident | The policy matched that application log |
| Received email | The notification reached the configured inbox |

The application log included a request ID, event timestamp, receipt timestamp, source ID and classification. The incident and email identified the same deployed revision. Together, these observations supported the complete path for this single test.

I retained the request and response, logs, policy creation input, service configuration and service IAM policy as JSON. Email and incident screenshots were separate evidence. I did not publish raw configuration exports because they can contain account identities and project identifiers.

## A late-event alert cannot see silence

This experiment sent a delayed event into a working receiver. It did not simulate a source disappearing.

If the source sends nothing, the receiver has no new event to classify and this filter has no warning to match. Detecting that case requires a separate signal, such as independently evaluated last-seen state or a suitable missing-data metric design.

A local process watchdog is also not automatically a cloud solution. A Cloud Run service can scale to zero, and multiple instances complicate process-local state. The mechanism needs to fit the deployment model.

Likewise, automatic incident closure does not prove that data recovered. A closed incident and a fresh incoming event are different observations. I would test recovery explicitly before promising that behavior to operators.

## Keep security and cleanup in the experiment

The receiver required IAM-authenticated invocation. The build and runtime service accounts were separate. The build account received the Cloud Run builder role; I granted no project role to the runtime account. The test request used the signed-in project operator's ID token. This run did not repeat the earlier dedicated-caller authorization experiment.

After saving evidence, I deleted the service, container repository, source bucket, alert policy, notification channel and two lab accounts, and removed the build-role binding. Resource listings confirmed zero services, repositories, buckets, policies and channels for the project. The default Compute Engine account remained.

This cleanup is evidence of resource removal, not evidence of a zero bill. Final costs were not measured.

The useful outcome was a reproducible check of one operational path: a valid request containing late test data produced a classified log, an incident and a delivered email. It is a starting point for testing observability behavior, with clearly recorded limits.

## Reproduce the experiment

The [GridPulse Lab guide](cloud-run-log-alert-validation.md) contains the filter, request example, observed results and cleanup sequence. It links to the receiver source and earlier IAM validation.

If you reproduce it, report whether the response, log, incident and email agree, and include your source commit and region. Failed reproductions and corrections are useful too. Remove tokens, email addresses and private project details before sharing evidence.

### References

- [Google Cloud: Configure log-based alerting policies](https://docs.cloud.google.com/logging/docs/alerting/log-based-alerts)
- [Google Cloud: Cloud Run logging](https://docs.cloud.google.com/run/docs/logging)
- [Google Cloud: Service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)

Publication status: article draft for review. The underlying experiment guide is public; this article has not been submitted to an editorial outlet.
