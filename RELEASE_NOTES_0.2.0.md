# GridPulse Lab v0.2.0 — Observability & Telemetry Health

GridPulse Lab v0.2.0 expands the project from basic telemetry simulation into a reproducible lab for detecting silent real-time data failures.

## Highlights

- progression detection distinguishes healthy timestamp advancement from unchanged and frozen streams;
- the `frozen_stream` training incident reproduces a stream whose values and timestamps stop advancing;
- `/metrics` exposes dependency-free Prometheus-format telemetry-health metrics;
- processing lag is measured and documented separately from telemetry freshness and progression;
- starter Prometheus and Grafana examples make the health signals observable locally;
- PromQL examples cover stale telemetry, frozen streams, fleet alarms, worst telemetry age, processing lag and quality counts;
- demonstration alerting rules show how stale, frozen, alarm and lag conditions can be surfaced;
- contributor onboarding and a focused beginner task make the project easier to extend.

All assets and telemetry are fictional or generated. The project contains no production endpoints, employer data or proprietary operational configuration.
