"""Controlled fault injection for demonstrations and testing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from .models import AssetTelemetry


class IncidentType(StrEnum):
    STALE = "stale"
    BAD_FREQUENCY = "bad_frequency"
    MISSING_SOC = "missing_soc"
    HIGH_TEMPERATURE = "high_temperature"


@dataclass(slots=True)
class ActiveIncident:
    asset_id: str
    kind: IncidentType


class IncidentController:
    def __init__(self) -> None:
        self._active: dict[str, ActiveIncident] = {}

    def activate(self, asset_id: str, kind: IncidentType) -> ActiveIncident:
        incident = ActiveIncident(asset_id, kind)
        self._active[asset_id] = incident
        return incident

    def clear(self, asset_id: str) -> None:
        self._active.pop(asset_id, None)

    def list(self) -> list[ActiveIncident]:
        return list(self._active.values())

    def apply(self, assets: list[AssetTelemetry]) -> list[AssetTelemetry]:
        for asset in assets:
            incident = self._active.get(asset.asset_id)
            if not incident:
                continue
            if incident.kind is IncidentType.STALE:
                for point in asset.points.values():
                    point.timestamp -= timedelta(minutes=5)
            elif incident.kind is IncidentType.BAD_FREQUENCY:
                asset.points["frequency"].value = 58.9
            elif incident.kind is IncidentType.MISSING_SOC:
                asset.points["soc"].value = None
            elif incident.kind is IncidentType.HIGH_TEMPERATURE:
                asset.points["temperature"].value = 72.0
        return assets
