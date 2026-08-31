# API reference

The development server exposes JSON endpoints under `/api/v1` plus a dependency-free Prometheus endpoint at `/metrics`.

## `GET /health`

Returns service readiness.

## `GET /telemetry`

Returns the generation timestamp, quality counts, progression counts and all fleet assets. Each point
has `value`, `unit`, UTC `timestamp` and `quality` fields. Each asset also includes a
`progression` object that reports whether observations are still advancing.

Quality values:

| Value | Meaning |
|---|---|
| `good` | Present, fresh and inside its configured range |
| `stale` | Timestamp exceeds the freshness threshold |
| `bad` | Value is outside its engineering range |
| `missing` | Value is unavailable |

Progression values:

| Value | Meaning |
|---|---|
| `progressing` | A newer observation timestamp has arrived |
| `unchanged` | The observation timestamp has not advanced yet, but is still inside the configured freeze window |
| `frozen` | The observation timestamp has failed to advance beyond the configured freeze window |

Progression is based on observation timestamps rather than value changes. A measurement can therefore
remain numerically constant and still be considered healthy when fresh observations continue to arrive.

## `GET /metrics`

Returns Prometheus text exposition format without requiring the Prometheus Python client.

Metrics:

| Metric | Meaning |
|---|---|
| `gridpulse_telemetry_age_seconds` | Age of the newest observation for each fictional asset |
| `gridpulse_active_alarms` | Number of active derived alarms |
| `gridpulse_active_incidents` | Number of active synthetic incidents |
| `gridpulse_quality_points` | Telemetry point count grouped by quality state |
| `gridpulse_progression_state` | One-hot progression state for each asset |

Example:

```text
# TYPE gridpulse_active_alarms gauge
gridpulse_active_alarms 0
gridpulse_telemetry_age_seconds{asset_id="aurora-1",region="North"} 0.0
gridpulse_progression_state{asset_id="aurora-1",status="progressing"} 1
```

The labels intentionally use a small, bounded set of fictional asset IDs and states to avoid unnecessary metric cardinality.

## `POST /incidents`

Activate or replace an incident for one asset.

```json
{
  "asset_id": "aurora-1",
  "kind": "bad_frequency"
}
```

Supported kinds are `stale`, `frozen_stream`, `bad_frequency`, `missing_soc`, and
`high_temperature`.

`frozen_stream` keeps observation timestamps fixed so the progression engine can demonstrate a feed
that appears present but has stopped advancing.

## `DELETE /incidents/{asset_id}`

Clear the active incident for an asset.
