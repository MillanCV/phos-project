from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from src.application.ports import CameraGateway, SchedulerGateway, StorageGateway, TimelapsePlanRepository
from src.domain.errors import NotFoundError, ValidationError
from src.domain.models import TimelapsePlan


class TimelapseManager:
    def __init__(
        self,
        camera_gateway: CameraGateway,
        storage_gateway: StorageGateway,
        scheduler_gateway: SchedulerGateway,
        plan_repository: TimelapsePlanRepository,
    ) -> None:
        self._camera_gateway = camera_gateway
        self._storage_gateway = storage_gateway
        self._scheduler_gateway = scheduler_gateway
        self._plan_repository = plan_repository
        self._lock = Lock()

    def bootstrap_active_plans(self) -> None:
        for plan in self._plan_repository.list_all():
            if plan.active:
                self._schedule_plan(plan)

    def create_plan(self, interval_seconds: int, window_start_hour: int, window_end_hour: int) -> TimelapsePlan:
        if interval_seconds < 10:
            raise ValidationError("interval_seconds must be >= 10")
        for value in (window_start_hour, window_end_hour):
            if value < 0 or value > 23:
                raise ValidationError("window hours must be in 0..23")

        plan = TimelapsePlan.new(interval_seconds, window_start_hour, window_end_hour)
        return self._plan_repository.save(plan)

    def get_plan(self, plan_id: str) -> TimelapsePlan:
        plan = self._plan_repository.get(plan_id)
        if not plan:
            raise NotFoundError(f"plan {plan_id} not found")
        return plan

    def start_plan(self, plan_id: str) -> TimelapsePlan:
        plan = self.get_plan(plan_id)
        if plan.active:
            return plan
        plan.active = True
        saved = self._plan_repository.save(plan)
        self._schedule_plan(saved)
        return saved

    def stop_plan(self, plan_id: str) -> TimelapsePlan:
        plan = self.get_plan(plan_id)
        if not plan.active:
            return plan
        plan.active = False
        saved = self._plan_repository.save(plan)
        self._scheduler_gateway.cancel(plan_id)
        return saved

    def _schedule_plan(self, plan: TimelapsePlan) -> None:
        self._scheduler_gateway.schedule_repeating(
            job_id=plan.id,
            interval_seconds=plan.interval_seconds,
            callback=lambda: self._execute_capture(plan.id),
        )

    def _execute_capture(self, plan_id: str) -> None:
        with self._lock:
            plan = self._plan_repository.get(plan_id)
            if not plan or not plan.active:
                self._scheduler_gateway.cancel(plan_id)
                return

            now = datetime.now(timezone.utc)
            if not plan.should_capture_now(now):
                return

            photo_path = self._camera_gateway.capture_photo()
            self._storage_gateway.register_capture(photo_path, source=f"timelapse:{plan.id}")
            plan.last_capture_at = now
            self._plan_repository.save(plan)
