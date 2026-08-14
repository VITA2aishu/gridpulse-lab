# API reference

The development server exposes a small JSON API under `/api/v1`.

## `GET /health`

Returns service readiness.

## `GET /telemetry`

Returns the generation timestamp, quality counts and all fleet assets. Each point
has `value`, `unit`, UTC `timestamp` and `quality` fields.

Quality values:

| Value | Meaning |
|---|---|
| `good` | Present, fresh and inside its configured range |
| `stale` | Timestamp exceeds the freshness threshold |
| `bad` | Value is outside its engineering range |
| `missing` | Value is unavailable |

## `POST /incidents`

Activate or replace an incident for one asset.

```json
{
  "asset_id": "aurora-1",
  "kind": "bad_frequency"
}
```

Supported kinds are `stale`, `bad_frequency`, `missing_soc`, and
`high_temperature`.

## `DELETE /incidents/{asset_id}`

Clear the active incident for an asset.

