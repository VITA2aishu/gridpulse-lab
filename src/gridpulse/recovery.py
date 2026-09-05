"""Track transitions from unhealthy telemetry states back to healthy operation."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from .health import HealthResult, HealthStatus


@dataclass(slots=True)
class _RecoveryState:
    previous_status: HealthStatus
    recovery_count: int = 0
    last_recovered_at: datetime | None = None


class RecoveryTracker:
    """Record when an asset returns to healthy after an unhealthy state."""

    def __init__(self) -> None:
        self._states: dict[str, _RecoveryState] = {}
        self._lock = threading.Lock()

    def evaluate(
        self,
        asset_id: str,
        health: HealthResult,
        now: datetime,
    ) -> dict[str, object]:
        with self._lock:
            state = self._states.get(asset_id)
            recovered = False

            if state is None:
                state = _RecoveryState(previous_status=health.status)
                self._states[asset_id] = state
            else:
                recovered = (
                    state.previous_status is not HealthStatus.HEALTHY
                    and health.status is HealthStatus.HEALTHY
                )
                if recovered:
                    state.recovery_count += 1
                    state.last_recovered_at = now
                state.previous_status = health.status

            return {
                "recovered": recovered,
                "recovery_count": state.recovery_count,
                "last_recovered_at": (
                    state.last_recovered_at.astimezone(timezone.utc).isoformat()
                    if state.last_recovered_at is not None
                    else None
                ),
            }
