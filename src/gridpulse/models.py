"""Domain models shared by the simulator, quality engine and API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Quality(StrEnum):
    GOOD = "good"
    STALE = "stale"
    BAD = "bad"
    MISSING = "missing"


@dataclass(slots=True)
class TelemetryPoint:
    value: float | int | bool | None
    unit: str
    timestamp: datetime
    quality: Quality = Quality.GOOD

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
        result["quality"] = self.quality.value
        return result


@dataclass(slots=True)
class AssetTelemetry:
    asset_id: str
    name: str
    region: str
    capacity_mw: float
    energy_mwh: float
    points: dict[str, TelemetryPoint]

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "region": self.region,
            "capacity_mw": self.capacity_mw,
            "energy_mwh": self.energy_mwh,
            "points": {key: point.to_dict() for key, point in self.points.items()},
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

