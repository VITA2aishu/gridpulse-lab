"""Detect whether telemetry observations continue to advance over time."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from .models import AssetTelemetry


class ProgressionStatus(StrEnum):
    PROGRESSING = "progressing"
    UNCHANGED = "unchanged"
    FROZEN = "frozen"


@dataclass(slots=True)
class _ProgressState:
    observation_at: datetime
    last_progress_at: datetime


class ProgressionEngine:
    """Track observation timestamps independently from telemetry values.

    A value can legitimately remain constant while its observation timestamp keeps
    advancing. A stream is considered frozen only when the newest observation
    timestamp fails to advance for longer than ``frozen_after``.
    """

    def __init__(self, frozen_after: timedelta = timedelta(seconds=10)) -> None:
        self.frozen_after = frozen_after
        self._states: dict[str, _ProgressState] = {}
        self._lock = threading.Lock()

    def evaluate(self, asset: AssetTelemetry, now: datetime) -> dict[str, object]:
        observation_at = max(point.timestamp for point in asset.points.values())

        with self._lock:
            state = self._states.get(asset.asset_id)
            if state is None:
                state = _ProgressState(observation_at, now)
                self._states[asset.asset_id] = state
                status = ProgressionStatus.PROGRESSING
            elif observation_at > state.observation_at:
                state.observation_at = observation_at
                state.last_progress_at = now
                status = ProgressionStatus.PROGRESSING
            else:
                elapsed = now - state.last_progress_at
                status = (
                    ProgressionStatus.FROZEN
                    if elapsed > self.frozen_after
                    else ProgressionStatus.UNCHANGED
                )

            seconds_since_progress = max(0.0, (now - state.last_progress_at).total_seconds())
            return {
                "status": status.value,
                "last_observation_at": state.observation_at.astimezone(timezone.utc).isoformat(),
                "seconds_since_progress": round(seconds_since_progress, 3),
                "frozen_after_seconds": self.frozen_after.total_seconds(),
            }
