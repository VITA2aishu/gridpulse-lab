"""Processing-lag measurement kept separate from source telemetry freshness."""

from __future__ import annotations

from datetime import datetime

from .models import AssetTelemetry


def processing_lag_seconds(asset: AssetTelemetry, processed_at: datetime) -> float:
    """Return delay from the newest observation to application processing."""
    newest = max(point.timestamp for point in asset.points.values())
    return max(0.0, (processed_at - newest).total_seconds())
