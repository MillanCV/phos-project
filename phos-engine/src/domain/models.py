from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4


CameraConnection = Literal["connected", "disconnected", "error"]


@dataclass(slots=True)
class CameraStatus:
    connection: CameraConnection
    model: str | None = None
    battery_percent: int | None = None
    last_error: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class CaptureRecord:
    id: str
    file_path: str
    captured_at: datetime
    source: str = "camera"


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


@dataclass(slots=True)
class SystemMetrics:
    disk_free_bytes: int
    disk_total_bytes: int
    cpu_load_1m: float
    temperature_c: float | None
    uptime_seconds: float
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def capture_record_from_path(path: Path, source: str = "camera") -> CaptureRecord:
    return CaptureRecord(
        id=str(uuid4()),
        file_path=str(path),
        captured_at=datetime.now(timezone.utc),
        source=source,
    )
