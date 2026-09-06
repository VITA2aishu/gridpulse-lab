# GridPulse Lab Roadmap

GridPulse Lab is an open-source learning project for real-time telemetry reliability, grid operations concepts, and battery energy storage system (BESS) monitoring using only synthetic data.

The project is intentionally small enough to run locally while still exposing the failure modes that make real-time applications difficult to operate.

## Project goals

1. Make stale, delayed, invalid, and unavailable telemetry easy to reproduce.
2. Provide a practical health model that goes beyond process uptime.
3. Give contributors approachable issues involving Python, APIs, observability, testing, and energy-system simulations.
4. Keep every example safe for public use by relying on fictional assets and generated data.
5. Make experiments reproducible so users can compare telemetry-health behavior and share results.

## Health model

GridPulse Lab evaluates five data-health signals:

- **Freshness** — how old is the newest valid observation?
- **Progression** — are new observations still arriving?
- **Connectivity** — is the expected source or interface available?
- **Processing lag** — how far behind real time is the pipeline?
- **Data quality** — is the information usable and internally consistent?

These signals feed a per-asset health score and a status of `healthy`, `degraded`, `stale`, or `failed`. The API also reports recovery metadata when an asset returns to healthy operation after an unhealthy state.

## v0.2 — Data health and observability

Completed in v0.2.0:

- Progression detection using observation timestamps.
- Synthetic frozen-stream incidents.
- Per-asset processing-lag calculation.
- Prometheus telemetry-health metrics.
- Prometheus and Grafana observability examples.
- Practical PromQL and alerting examples.
- Expanded contributor documentation and tests.

## v0.3 — Combined telemetry health

Completed on `main`:

- Combined freshness, progression, connectivity, processing lag, and data quality into a per-asset health assessment.
- Exposed health score, status, and underlying signals through the API.
- Exported combined health score/state through Prometheus metrics.
- Surfaced combined health in the local dashboard.
- Added focused tests for healthy, degraded, stale, frozen, bad-quality, and unavailable scenarios.
- Added recovery-state tracking for transitions back to healthy operation.

## v0.4 — Extensibility and reproducibility

Planned work should prioritize features that make the lab easier for other people to configure, test, and evaluate:

- Configurable fictional assets loaded from JSON.
- Contributor-defined incident scenarios.
- Pluggable validation rules.
- Example integrations that consume the public API without coupling to simulator internals.
- Reproducible scenario runs with machine-readable results that can be compared across versions.

## Community goals

GridPulse Lab should become a useful practice environment, not just a demo repository. Contributions that improve tests, documentation, accessibility, reliability, observability, synthetic scenarios, or reproducibility are welcome.

The project especially welcomes independent scenario reports and integrations that show how the telemetry-health signals behave in different synthetic conditions. Findings do not need to be positive; reproducible limitations and failure cases are useful contributions too.

If you are new to the project, start with `CONTRIBUTING.md` and the open issues. Small, well-tested improvements are preferred over large rewrites.
