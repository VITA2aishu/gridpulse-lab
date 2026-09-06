# Independent evaluation guide

This guide provides a small, repeatable evaluation for GridPulse Lab. It is
designed for external users who want to verify telemetry-health behavior rather
than rely on screenshots or project claims.

## 1. Record the version

```bash
python -c "import gridpulse; print(gridpulse.__version__)"
```

When running from a source checkout, also record `git rev-parse HEAD`.

## 2. Start the lab

```bash
PYTHONPATH=src python -m gridpulse.server
```

In another terminal, save the initial fleet response:

```bash
curl -s http://127.0.0.1:8080/api/v1/telemetry
```

Confirm that the fictional assets report health information and that
`http://127.0.0.1:8080/metrics` returns Prometheus-format metrics.

## 3. Reproduce a silent frozen stream

```bash
curl -s -X POST http://127.0.0.1:8080/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"aurora-1","kind":"frozen_stream"}'
```

Observe at least two subsequent telemetry responses. Record whether timestamps
and values stop progressing and whether the health signals expose the failure.

## 4. Verify recovery

```bash
curl -s -X DELETE http://127.0.0.1:8080/api/v1/incidents/aurora-1
```

Observe subsequent responses and record whether the asset returns to healthy
operation and exposes recovery metadata.

## 5. Share reproducible findings

Use the [independent use report](https://github.com/VITA2aishu/gridpulse-lab/issues/new?template=independent-use.yml).
Include the version, operating system, Python version, commands used, observed
results and any expected behavior that did not occur. Both successful results
and reproducible limitations are valuable.

Only synthetic or public data may be used. Never attach employer, customer,
plant, endpoint, credential, or production information.
