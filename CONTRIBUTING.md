# Contributing to GridPulse Lab

Thank you for helping make grid operations concepts more accessible. Beginner
contributions are welcome, especially documentation, tests and new synthetic
incident scenarios.

## Development workflow

1. Fork the repository and create a focused branch.
2. Make one logically complete change.
3. Run `PYTHONPATH=src python -m unittest discover -s tests -v`.
4. Open a pull request explaining the operational concept and test evidence.

Please never submit real plant names, credentials, endpoints, screenshots,
telemetry or employer-specific configurations. All examples must be fictional or
clearly generated.

## Good first contributions

- add a voltage point with an engineering-range test;
- make the simulator tick interval configurable;
- add keyboard and screen-reader checks to the dashboard;
- document a new synthetic incident scenario.

