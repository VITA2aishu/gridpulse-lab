# GridPulse Lab

[![CI](https://github.com/VITA2aishu/gridpulse-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/VITA2aishu/gridpulse-lab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-45e0a8)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-45e0a8.svg)](LICENSE)

An open-source, dependency-free lab for learning how real-time grid and battery
energy storage telemetry behaves when measurements become stale, invalid or
unavailable.

> **Safety note:** GridPulse Lab uses generated data and fictional assets. It
> contains no employer data, production endpoints or proprietary configuration.

## Why it exists

Operational energy systems are difficult to learn without access to a control
room. GridPulse Lab makes the important concepts reproducible on a laptop:

- battery state of charge, active/reactive power and frequency;
- telemetry freshness and data-quality evaluation;
- alarm lifecycle and incident injection;
- a live operations dashboard and documented JSON API.

## Quick start

```bash
python -m gridpulse.server
```

Then open <http://localhost:8080>. For source checkouts without installation:

```bash
PYTHONPATH=src python -m gridpulse.server
```

Run the test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Project status

The first release includes a live three-asset fleet, four injectable incidents,
quality evaluation, derived alarms, a responsive dashboard and automated tests.

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Service readiness |
| `GET /api/v1/telemetry` | Fleet snapshot, quality summary and alarms |
| `GET /api/v1/incidents` | Active training incidents |
| `POST /api/v1/incidents` | Activate an incident |
| `DELETE /api/v1/incidents/{asset_id}` | Clear an incident |

See the [API reference](docs/api.md) and [architecture](docs/architecture.md).

## Roadmap

- time-series history and incident replay;
- configurable custom assets;
- optional Prometheus metrics exporter;
- battery efficiency and degradation models;
- community-contributed training scenarios.

Contributions are welcome. Start with the safety requirements and suggested
beginner issues in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
