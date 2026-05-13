from __future__ import annotations

from datetime import datetime, timezone
import os
from threading import Lock

from src.camera.domain import CameraManualSettings, CameraManualState, CameraOperation
from src.camera.operation_queue import CameraOperationQueue
from src.camera.ports import CameraManualPort, CameraOperationPort
from src.shared.errors import NotFoundError, ValidationError


class CameraControlService(CameraOperationPort):
    """Application service for async camera control operations."""

    def __init__(
        self,
        manual_port: CameraManualPort,
        operation_queue: CameraOperationQueue,
        sleep_after_seconds: int = 60,
        deep_sleep_after_seconds: int = 600,
    ) -> None:
        if sleep_after_seconds <= 0 or deep_sleep_after_seconds <= 0:
            raise ValidationError("sleep thresholds must be > 0")
        if deep_sleep_after_seconds <= sleep_after_seconds:
            raise ValidationError("deep sleep threshold must be greater than sleep threshold")
        self._manual_port = manual_port
        self._queue = operation_queue
        self._sleep_after_seconds = sleep_after_seconds
        self._deep_sleep_after_seconds = deep_sleep_after_seconds
        self._policy_lock = Lock()
        # When true, every GET /camera/manual/state runs idle→sleep logic (surprising with 15s UI polling).
        self._idle_policy_on_read = os.getenv("PHOS_CAMERA_IDLE_POLICY_ON_READ", "false").lower() == "true"

    def get_manual_state(self) -> CameraManualState:
        if self._idle_policy_on_read:
            self._run_idle_policy()
        return self._manual_port.get_manual_state()

    def touch(self) -> CameraManualState:
        return self._manual_port.touch()

    def submit_apply_manual_settings(self, settings: CameraManualSettings) -> CameraOperation:
        return self._queue.submit("apply_manual_settings", lambda: self._manual_port.apply_manual_settings(settings))

    def submit_sleep(self, level: str) -> CameraOperation:
        if level not in ("sleep", "deep_sleep"):
            raise ValidationError("sleep level must be 'sleep' or 'deep_sleep'")
        return self._queue.submit(f"sleep_{level}", lambda: self._manual_port.sleep(level))

    def submit_wake(self) -> CameraOperation:
        return self._queue.submit("wake", self._manual_port.wake)

    def get_operation(self, operation_id: str) -> CameraOperation | None:
        return self._queue.get(operation_id)

    def get_operation_required(self, operation_id: str) -> CameraOperation:
        operation = self.get_operation(operation_id)
        if operation is None:
            raise NotFoundError(f"camera operation {operation_id} not found")
        return operation

    def _run_idle_policy(self) -> None:
        with self._policy_lock:
            state = self._manual_port.get_manual_state()
            idle_seconds = int((datetime.now(timezone.utc) - state.last_interaction_at).total_seconds())
            if idle_seconds >= self._deep_sleep_after_seconds and state.power_state != "deep_sleep":
                self._manual_port.sleep("deep_sleep")
                return
            if idle_seconds >= self._sleep_after_seconds and state.power_state == "active":
                self._manual_port.sleep("sleep")
