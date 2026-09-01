# PromQL examples

These queries are educational examples for the fictional GridPulse Lab fleet. Thresholds are demonstration defaults, not production recommendations.

## Assets with stale telemetry

```promql
gridpulse_telemetry_age_seconds > 15
```

## Frozen streams

```promql
gridpulse_progression_state{status="frozen"} == 1
```

## Fleet alarm count

```promql
gridpulse_active_alarms
```

## Worst telemetry age

```promql
max(gridpulse_telemetry_age_seconds)
```

## Processing lag by asset

```promql
gridpulse_processing_lag_seconds
```

## Assets with elevated processing lag

```promql
gridpulse_processing_lag_seconds > 10
```

## Quality-point counts

```promql
gridpulse_quality_points
```

## Frozen assets by count

```promql
sum(gridpulse_progression_state{status="frozen"} == 1)
```

Use these queries as starting points while experimenting with the generated telemetry and incident scenarios in GridPulse Lab.
