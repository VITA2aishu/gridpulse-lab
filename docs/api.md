# API reference

The development server exposes a small JSON API under `/api/v1`.

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

Example asset progression payload:

```json
{
  "status": "progressing",
  "last_observation_at": "2026-08-31T23:40:00+00:00",
  "seconds_since_progress": 0.0,
  "frozen_after_seconds": 10.0
}
```

Progression is based on observation timestamps rather than value changes. A measurement can therefore
remain numerically constant and still be considered healthy when fresh observations continue to arrive.

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

