"""Derive human-readable alarms from evaluated telemetry quality."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import AssetTelemetry, Quality


class Severity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Alarm:
    alarm_id: str
    asset_id: str
    severity: Severity
    message: str
    point: str

    def to_dict(self) -> dict[str, str]:
        return {
            "alarm_id": self.alarm_id,
            "asset_id": self.asset_id,
            "severity": self.severity.value,
            "message": self.message,
            "point": self.point,
        }


def derive_alarms(assets: list[AssetTelemetry]) -> list[Alarm]:
    alarms: list[Alarm] = []
    for asset in assets:
        for name, point in asset.points.items():
            if point.quality is Quality.GOOD:
                continue
            severity = Severity.CRITICAL if point.quality in (Quality.BAD, Quality.MISSING) else Severity.WARNING
            readable_name = name.replace("_", " ").title()
            alarms.append(Alarm(
                alarm_id=f"{asset.asset_id}:{name}:{point.quality.value}",
                asset_id=asset.asset_id,
                severity=severity,
                message=f"{readable_name} quality is {point.quality.value}",
                point=name,
            ))
    return alarms

