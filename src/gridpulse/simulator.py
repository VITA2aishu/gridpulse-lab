"""Deterministic synthetic telemetry for a small fictional BESS fleet."""

from __future__ import annotations

import math
import random
import threading
from dataclasses import dataclass
from datetime import datetime

from .models import AssetTelemetry, TelemetryPoint, utc_now


@dataclass(frozen=True, slots=True)
class AssetConfig:
    asset_id: str
    name: str
    region: str
    capacity_mw: float
    energy_mwh: float
    initial_soc: float


DEFAULT_FLEET = (
    AssetConfig("aurora-1", "Aurora BESS", "North", 100.0, 200.0, 68.0),
    AssetConfig("bluebonnet-1", "Bluebonnet Storage", "Central", 75.0, 150.0, 51.0),
    AssetConfig("canyon-1", "Canyon Reserve", "West", 50.0, 100.0, 82.0),
)


class FleetSimulator:
    """Thread-safe fleet simulator with repeatable output for a given seed."""

    def __init__(self, seed: int = 42, fleet: tuple[AssetConfig, ...] = DEFAULT_FLEET):
        self._random = random.Random(seed)
        self._fleet = fleet
        self._step = 0
        self._soc = {asset.asset_id: asset.initial_soc for asset in fleet}
        self._lock = threading.Lock()

    def snapshot(self, timestamp: datetime | None = None) -> list[AssetTelemetry]:
        with self._lock:
            self._step += 1
            now = timestamp or utc_now()
            return [self._simulate_asset(asset, now) for asset in self._fleet]

    def _simulate_asset(self, asset: AssetConfig, now: datetime) -> AssetTelemetry:
        phase = self._step / 8 + list(self._fleet).index(asset) * 1.7
        power = asset.capacity_mw * 0.62 * math.sin(phase)
        power += self._random.uniform(-1.2, 1.2)
        power = round(max(-asset.capacity_mw, min(asset.capacity_mw, power)), 2)

        # Positive MW represents discharge; negative MW represents charge.
        hours_per_tick = 2 / 3600
        soc_delta = -(power * hours_per_tick / asset.energy_mwh) * 100
        self._soc[asset.asset_id] = max(5.0, min(95.0, self._soc[asset.asset_id] + soc_delta))

        frequency = round(60 + self._random.gauss(0, 0.018), 3)
        reactive = round(power * 0.08 + self._random.uniform(-0.8, 0.8), 2)
        temperature = round(25 + abs(power) / asset.capacity_mw * 9 + self._random.uniform(-0.4, 0.4), 1)

        def point(value: float | bool, unit: str) -> TelemetryPoint:
            return TelemetryPoint(value=value, unit=unit, timestamp=now)

        return AssetTelemetry(
            asset_id=asset.asset_id,
            name=asset.name,
            region=asset.region,
            capacity_mw=asset.capacity_mw,
            energy_mwh=asset.energy_mwh,
            points={
                "soc": point(round(self._soc[asset.asset_id], 2), "%"),
                "active_power": point(power, "MW"),
                "reactive_power": point(reactive, "MVAR"),
                "frequency": point(frequency, "Hz"),
                "temperature": point(temperature, "°C"),
                "breaker_closed": point(abs(power) > 0.25, "bool"),
            },
        )
