"""Prometheus text exporter for GridPulse telemetry health."""

from __future__ import annotations

from datetime import datetime

from .health import HealthResult
from .lag import processing_lag_seconds
from .models import AssetTelemetry, Quality


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _sample(name: str, value: int | float, **labels: str) -> str:
    if labels:
        rendered = ",".join(f'{key}="{_escape(label)}"' for key, label in labels.items())
        return f"{name}{{{rendered}}} {value}"
    return f"{name} {value}"


def render_metrics(
    assets: list[AssetTelemetry],
    progression: dict[str, dict[str, object]],
    health: dict[str, HealthResult],
    alarm_count: int,
    incident_count: int,
    now: datetime,
) -> str:
    """Render a compact Prometheus 0.0.4-compatible metrics payload."""
    lines = [
        "# HELP gridpulse_active_alarms Number of active derived alarms.",
        "# TYPE gridpulse_active_alarms gauge",
        _sample("gridpulse_active_alarms", alarm_count),
        "# HELP gridpulse_active_incidents Number of active synthetic incidents.",
        "# TYPE gridpulse_active_incidents gauge",
        _sample("gridpulse_active_incidents", incident_count),
        "# HELP gridpulse_telemetry_age_seconds Age of the newest observation for an asset.",
        "# TYPE gridpulse_telemetry_age_seconds gauge",
    ]

    for asset in assets:
        newest = max(point.timestamp for point in asset.points.values())
        age = max(0.0, (now - newest).total_seconds())
        labels = {"asset_id": asset.asset_id, "region": asset.region}
        lines.append(_sample("gridpulse_telemetry_age_seconds", round(age, 3), **labels))

    lines.extend([
        "# HELP gridpulse_processing_lag_seconds Delay from newest observation to application processing.",
        "# TYPE gridpulse_processing_lag_seconds gauge",
    ])
    for asset in assets:
        lines.append(_sample(
            "gridpulse_processing_lag_seconds",
            round(processing_lag_seconds(asset, now), 3),
            asset_id=asset.asset_id,
            region=asset.region,
        ))

    lines.extend([
        "# HELP gridpulse_quality_points Number of telemetry points by quality state.",
        "# TYPE gridpulse_quality_points gauge",
    ])
    for quality in Quality:
        count = sum(point.quality is quality for asset in assets for point in asset.points.values())
        lines.append(_sample("gridpulse_quality_points", count, quality=quality.value))

    lines.extend([
        "# HELP gridpulse_progression_state Asset progression state encoded as a one-hot gauge.",
        "# TYPE gridpulse_progression_state gauge",
    ])
    states = ("progressing", "unchanged", "frozen")
    for asset in assets:
        current = str(progression[asset.asset_id]["status"])
        for state in states:
            lines.append(_sample(
                "gridpulse_progression_state",
                1 if current == state else 0,
                asset_id=asset.asset_id,
                status=state,
            ))

    lines.extend([
        "# HELP gridpulse_health_score Combined telemetry-health score from 0 to 100.",
        "# TYPE gridpulse_health_score gauge",
        "# HELP gridpulse_health_state Combined asset health state encoded as a one-hot gauge.",
        "# TYPE gridpulse_health_state gauge",
    ])
    health_states = ("healthy", "degraded", "stale", "failed")
    for asset in assets:
        result = health[asset.asset_id]
        lines.append(_sample(
            "gridpulse_health_score",
            result.score,
            asset_id=asset.asset_id,
            region=asset.region,
        ))
        for state in health_states:
            lines.append(_sample(
                "gridpulse_health_state",
                1 if result.status.value == state else 0,
                asset_id=asset.asset_id,
                status=state,
            ))

    return "\n".join(lines) + "\n"
