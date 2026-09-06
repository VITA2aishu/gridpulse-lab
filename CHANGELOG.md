# Changelog

All notable changes to GridPulse Lab are documented here.

## [0.3.0] - Unreleased

### Added

- combined health scoring across freshness, progression, connectivity, processing lag and data quality;
- health status and component signals in the API, dashboard and Prometheus metrics;
- recovery-state tracking when an asset returns to healthy operation;
- a public evaluation guide and structured independent-use reporting process;
- citation metadata for research and technical reports.

## [0.2.0] - 2026-09-01

### Added

- telemetry progression detection that distinguishes progressing, unchanged and frozen streams;
- a synthetic `frozen_stream` incident for reproducing silent telemetry failures;
- Prometheus-format telemetry-health metrics at `/metrics`;
- per-asset processing-lag measurement kept distinct from freshness and progression;
- a starter Prometheus scrape configuration and importable Grafana telemetry-health dashboard;
- practical PromQL examples for stale telemetry, frozen streams, fleet alarms, worst telemetry age, processing lag and quality counts;
- demonstration Prometheus alerting rules for stale telemetry, frozen progression, active alarms and elevated processing lag;
- an observability quick start and illustrative dashboard preview;
- contributor onboarding and focused beginner contribution guidance.

### Safety

- examples, telemetry and asset identifiers remain generated or fictional;
- no production endpoints, employer data or proprietary operational configuration are included.

## [0.1.0]

Initial GridPulse Lab release with a dependency-free Python server, fictional telemetry simulator, quality evaluation, alarm handling, synthetic incidents, dashboard, API documentation and automated tests.
