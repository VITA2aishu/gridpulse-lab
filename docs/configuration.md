# Fleet asset configuration

GridPulse Lab ships with a built-in fictional fleet of three battery assets.
Workshops, demos and tests can model a different fictional fleet by pointing
the server at a local JSON configuration file — no code changes required.

## Usage

```bash
PYTHONPATH=src python -m gridpulse.server --assets examples/assets/workshop-fleet.json
```

Or with the installed package:

```bash
gridpulse --assets path/to/fleet.json
```

When `--assets` is omitted, the built-in fictional fleet is used unchanged.
A runnable example lives at
[`examples/assets/workshop-fleet.json`](../examples/assets/workshop-fleet.json).

## File format

The file holds one JSON object with a single `"assets"` array. Each entry
describes one fictional asset:

```json
{
  "assets": [
    {
      "asset_id": "harbor-1",
      "name": "Harbor Point Battery",
      "region": "East",
      "capacity_mw": 60,
      "energy_mwh": 240,
      "initial_soc": 55
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `asset_id` | string | yes | Unique lowercase slug of letters, digits and single dashes (at most 64 characters), e.g. `"aurora-1"`. Used in API payloads and metric labels. |
| `name` | string | yes | Fictional display name shown in the dashboard and API. |
| `region` | string | yes | Fictional region label, also exported as a metric label. |
| `capacity_mw` | number | yes | Nameplate power limit in MW. Must be greater than 0. |
| `energy_mwh` | number | yes | Usable energy capacity in MWh. Must be greater than 0. |
| `initial_soc` | number | no | Starting state of charge in percent, 0–100. Defaults to `50`. |

Additional rules:

- `"assets"` is the only supported top-level field and must be a non-empty array.
- A fleet may declare at most 50 assets so dashboards and metric labels stay low-cardinality.
- Asset ids must be unique within the file.
- The simulator keeps state of charge inside 5–95% while running, so
  `initial_soc` only selects the starting point.
- All assets use the existing battery telemetry model; the file cannot change
  point names, units or update behaviour.

## Validation errors

Malformed or unsupported input stops startup with a message that names the
offending field, for example:

```text
gridpulse.server: error: 'fleet.json' is not valid JSON: Expecting ',' delimiter: line 4 column 5 (char 88)
gridpulse.server: error: assets[0]: missing required field 'capacity_mw'
gridpulse.server: error: assets[1].initial_soc: expected a value between 0 and 100, got 120
gridpulse.server: error: assets[1].asset_id: duplicate asset id 'aurora-1'
```

Reading the file with `gridpulse.config.load_fleet` raises the same messages as
`AssetConfigError` for programmatic use and testing.

## Safety

Configuration files must describe fictional assets only. Do not include real
plant names, customer data, production endpoints, credentials or network
details — the same boundary that applies to all GridPulse Lab examples.
