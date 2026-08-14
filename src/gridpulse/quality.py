"""Telemetry freshness and engineering-range evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import AssetTelemetry, Quality


@dataclass(frozen=True, slots=True)
class RangeRule:
    minimum: float
    maximum: float


DEFAULT_RULES = {
    "soc": RangeRule(0, 100),
    "frequency": RangeRule(59.5, 60.5),
    "temperature": RangeRule(-20, 65),
}


class QualityEngine:
    def __init__(self, stale_after: timedelta = timedelta(seconds=10)):
        self.stale_after = stale_after

    def evaluate(self, asset: AssetTelemetry, now: datetime) -> AssetTelemetry:
        """Mutate point quality in-place and return the asset for composition."""
        for name, point in asset.points.items():
            if point.value is None:
                point.quality = Quality.MISSING
            elif now - point.timestamp > self.stale_after:
                point.quality = Quality.STALE
            elif name in DEFAULT_RULES and isinstance(point.value, (int, float)):
                rule = DEFAULT_RULES[name]
                point.quality = (
                    Quality.GOOD if rule.minimum <= point.value <= rule.maximum else Quality.BAD
                )
            else:
                point.quality = Quality.GOOD
        return asset

    @staticmethod
    def summary(assets: list[AssetTelemetry]) -> dict[str, int]:
        counts = {quality.value: 0 for quality in Quality}
        for asset in assets:
            for point in asset.points.values():
                counts[point.quality.value] += 1
        return counts

