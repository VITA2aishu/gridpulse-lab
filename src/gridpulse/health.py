"""Combine telemetry signals into a concise per-asset health assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .lag import processing_lag_seconds
from .models import AssetTelemetry, Quality


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class HealthResult:
    score: int
    status: HealthStatus
    signals: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "status": self.status.value,
            "signals": self.signals,
        }


class HealthEngine:
    """Evaluate freshness, progression, connectivity, lag and data quality.

    The score is intentionally simple and deterministic so it remains useful for
    demonstrations. Individual signals are returned alongside the score so users
    can see *why* an asset is not healthy instead of relying on one opaque number.
    """

    def __init__(
        self,
        stale_after: timedelta = timedelta(seconds=10),
        high_lag_after: timedelta = timedelta(seconds=30),
    ) -> None:
        self.stale_after = stale_after
        self.high_lag_after = high_lag_after

    def evaluate(
        self,
        asset: AssetTelemetry,
        progression: dict[str, object],
        now: datetime,
    ) -> HealthResult:
        if not asset.points:
            return HealthResult(
                score=0,
                status=HealthStatus.FAILED,
                signals={
                    "freshness": "unknown",
                    "progression": str(progression.get("status", "unknown")),
                    "connectivity": "unavailable",
                    "processing_lag_seconds": None,
                    "data_quality": "unknown",
                },
            )

        newest = max(point.timestamp for point in asset.points.values())
        age = max(0.0, (now - newest).total_seconds())
        lag = processing_lag_seconds(asset, now)
        freshness = "fresh" if age <= self.stale_after.total_seconds() else "stale"
        progression_status = str(progression.get("status", "unknown"))

        qualities = [point.quality for point in asset.points.values()]
        problem_count = sum(quality is not Quality.GOOD for quality in qualities)
        if any(quality in (Quality.BAD, Quality.MISSING) for quality in qualities):
            data_quality = "bad"
        elif problem_count:
            data_quality = "degraded"
        else:
            data_quality = "good"

        score = 100
        if freshness == "stale":
            score -= 25
        if progression_status == "unchanged":
            score -= 10
        elif progression_status == "frozen":
            score -= 25
        elif progression_status not in {"progressing", "unchanged", "frozen"}:
            score -= 10

        if lag > self.high_lag_after.total_seconds():
            score -= 15
        elif lag > self.stale_after.total_seconds():
            score -= 8

        if data_quality == "bad":
            score -= 20
        elif data_quality == "degraded":
            score -= 10

        score = max(0, min(100, score))

        if freshness == "stale" or progression_status == "frozen":
            status = HealthStatus.STALE if score >= 30 else HealthStatus.FAILED
        elif data_quality != "good" or progression_status != "progressing" or score < 90:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthResult(
            score=score,
            status=status,
            signals={
                "freshness": freshness,
                "progression": progression_status,
                "connectivity": "available",
                "processing_lag_seconds": round(lag, 3),
                "data_quality": data_quality,
            },
        )
