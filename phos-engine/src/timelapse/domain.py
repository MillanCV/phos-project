from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class TimelapsePlan:
    id: str
    interval_seconds: int
    window_start_hour: int
    window_end_hour: int
    active: bool = False
    last_capture_at: datetime | None = None

    @staticmethod
    def new(interval_seconds: int, window_start_hour: int, window_end_hour: int) -> "TimelapsePlan":
        return TimelapsePlan(
            id=str(uuid4()),
            interval_seconds=interval_seconds,
            window_start_hour=window_start_hour,
            window_end_hour=window_end_hour,
        )

    def should_capture_now(self, now: datetime) -> bool:
        hour = now.hour
        if self.window_start_hour <= self.window_end_hour:
            in_window = self.window_start_hour <= hour < self.window_end_hour
        else:
            # Window crossing midnight, e.g. 22 -> 6.
            in_window = hour >= self.window_start_hour or hour < self.window_end_hour
        return in_window
