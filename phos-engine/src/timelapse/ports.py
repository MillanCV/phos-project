from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from src.timelapse.domain import TimelapsePlan


class SchedulerGateway(Protocol):
    def schedule_repeating(self, job_id: str, interval_seconds: int, callback: Callable[[], None]) -> None: ...

    def cancel(self, job_id: str) -> None: ...


class TimelapsePlanRepository(Protocol):
    def save(self, plan: TimelapsePlan) -> TimelapsePlan: ...

    def get(self, plan_id: str) -> TimelapsePlan | None: ...

    def list_all(self) -> list[TimelapsePlan]: ...
