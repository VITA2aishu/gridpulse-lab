# Contributing to GridPulse Lab

Thank you for helping make real-time telemetry and grid-operations concepts more accessible. Beginner contributions are welcome, especially documentation, tests, observability examples, and new synthetic incident scenarios.

## Start here

If this is your first contribution, pick one open issue labeled [`good first issue`](https://github.com/VITA2aishu/gridpulse-lab/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22). Current examples include:

- [#13 — Add exporter unit tests for escaping metric labels](https://github.com/VITA2aishu/gridpulse-lab/issues/13)
- [#14 — Document example PromQL queries](https://github.com/VITA2aishu/gridpulse-lab/issues/14)

Comment on the issue before starting if you want to confirm the approach or scope.

## Development workflow

1. Fork the repository and create a focused branch.
2. Make one logically complete change that addresses the issue or improvement.
3. Run `PYTHONPATH=src python -m unittest discover -s tests -v`.
4. Keep examples deterministic and dependency-free unless an issue explicitly says otherwise.
5. Open a pull request that explains what changed, why it helps, and how you tested it.

Small pull requests are preferred. A focused documentation fix or a few targeted tests are useful contributions and do not need to be bundled with unrelated changes.

## Pull request checklist

Before opening a pull request, confirm that:

- tests pass locally when the change affects code;
- new behavior has tests or clear documentation where appropriate;
- metric labels and examples remain low-cardinality and synthetic;
- documentation uses fictional asset names and reproducible commands;
- no real operational, employer, customer, or production information is included.

## Safety and data rules

Please never submit real plant names, credentials, endpoints, screenshots, telemetry, network details, customer information, employer-specific configurations, or other non-public operational data. All examples must be fictional or clearly generated.

If a contribution needs realistic-looking telemetry, extend the simulator or add synthetic fixtures rather than copying data from a real system.

## Useful local checks

Run the test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Start the local server:

```bash
PYTHONPATH=src python -m gridpulse.server
```

Then check the application at <http://localhost:8080> and Prometheus-format metrics at <http://localhost:8080/metrics>.

See the [observability guide](docs/observability.md) for the Prometheus and Grafana walkthrough.
