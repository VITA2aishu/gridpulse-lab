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

The longer-term health model goes beyond service uptime and focuses on five
signals: **freshness, progression, connectivity, processing lag and data
quality**. See the [public roadmap](ROADMAP.md) for planned releases and
contribution opportunities.

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

The next release focuses on detecting silent data failures, including frozen
streams, delayed processing and combined data-health scoring. See the
[open issues](https://github.com/VITA2aishu/gridpulse-lab/issues) if you would
like to contribute.

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

- data-health scoring across freshness, progression, connectivity, lag and quality;
- time-series history and incident replay;
- optional Prometheus metrics exporter;
- configurable fictional assets;
- community-contributed training scenarios.

Full details are tracked in [ROADMAP.md](ROADMAP.md).

Contributions are welcome. Start with the safety requirements and suggested
beginner issues in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
