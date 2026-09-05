# GridPulse Lab Roadmap

GridPulse Lab is an open-source learning project for real-time telemetry reliability, grid operations concepts, and battery energy storage system (BESS) monitoring using only synthetic data.

The project is intentionally small enough to run locally while still exposing the failure modes that make real-time applications difficult to operate.

## Project goals

1. Make stale, delayed, invalid, and unavailable telemetry easy to reproduce.
2. Provide a practical health model that goes beyond process uptime.
3. Give contributors approachable issues involving Python, APIs, observability, testing, and energy-system simulations.
4. Keep every example safe for public use by relying on fictional assets and generated data.

## Health model

GridPulse Lab is evolving around five data-health signals:

- **Freshness** — how old is the newest valid observation?
- **Progression** — are new observations still arriving?
- **Connectivity** — is the expected source or interface available?
- **Processing lag** — how far behind real time is the pipeline?
- **Data quality** — is the information usable and internally consistent?

These signals feed a per-source health score and a fleet-level status of `HEALTHY`, `DEGRADED`, `STALE`, or `FAILED`.

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

- Combine freshness, progression, connectivity, processing lag, and data quality into a per-asset health assessment.
- Expose the health score, status, and underlying signals through the API.
- Export combined health score/state through Prometheus metrics.
- Surface combined health clearly in the local dashboard.
- Add tests for healthy, degraded, stale, frozen, missing, and unavailable scenarios.
- Improve recovery-state tracking so health returns to normal when synthetic incidents clear.

## v0.4 — Extensibility

- Configurable fictional assets loaded from JSON.
- Contributor-defined incident scenarios.
- Pluggable validation rules.
- Example integrations that consume the public API without coupling to the simulator internals.

## Community goals

GridPulse Lab should become a useful practice environment, not just a demo repository. Contributions that improve tests, documentation, accessibility, reliability, observability, or synthetic scenarios are welcome.

If you are new to the project, start with `CONTRIBUTING.md` and the open issues. Small, well-tested improvements are preferred over large rewrites.
