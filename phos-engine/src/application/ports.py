from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from src.domain.models import CameraStatus, CaptureRecord, SystemMetrics, TimelapsePlan


class CameraGateway(Protocol):
    def get_status(self) -> CameraStatus: ...

    def capture_photo(self) -> Path: ...


class StorageGateway(Protocol):
    def register_capture(self, file_path: Path, source: str = "camera") -> CaptureRecord: ...

    def get_latest_capture(self) -> CaptureRecord | None: ...


class SchedulerGateway(Protocol):
    def schedule_repeating(self, job_id: str, interval_seconds: int, callback: Callable[[], None]) -> None: ...

    def cancel(self, job_id: str) -> None: ...


class TimelapsePlanRepository(Protocol):
    def save(self, plan: TimelapsePlan) -> TimelapsePlan: ...

    def get(self, plan_id: str) -> TimelapsePlan | None: ...

    def list_all(self) -> list[TimelapsePlan]: ...


class MetricsGateway(Protocol):
    def get_metrics(self) -> SystemMetrics: ...
