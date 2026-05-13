from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from queue import Queue
from threading import Lock, Thread
from uuid import uuid4

from src.camera.domain import CameraManualState, CameraOperation, CameraOperationState


OperationCallable = Callable[[], CameraManualState]


class CameraOperationQueue:
    """Serialize long-running camera operations in a background worker."""

    def __init__(self) -> None:
        self._queue: Queue[tuple[str, str, OperationCallable]] = Queue()
        self._operations: dict[str, CameraOperation] = {}
        self._lock = Lock()
        self._worker = Thread(target=self._work, daemon=True, name="camera-operation-worker")
        self._worker.start()

    def submit(self, operation_type: str, action: OperationCallable) -> CameraOperation:
        now = datetime.now(timezone.utc)
        operation = CameraOperation(
            operation_id=str(uuid4()),
            operation_type=operation_type,
            state="pending",
            submitted_at=now,
        )
        with self._lock:
            self._operations[operation.operation_id] = operation
        self._queue.put((operation.operation_id, operation_type, action))
        return operation

    def get(self, operation_id: str) -> CameraOperation | None:
        with self._lock:
            return self._operations.get(operation_id)

    def _work(self) -> None:
        while True:
            operation_id, operation_type, action = self._queue.get()
            started_at = datetime.now(timezone.utc)
            self._set_state(operation_id, "running", started_at=started_at)
            try:
                result = action()
                self._set_state(
                    operation_id,
                    "completed",
                    finished_at=datetime.now(timezone.utc),
                    manual_state=result,
                )
            except Exception as exc:  # noqa: BLE001
                self._set_state(
                    operation_id,
                    "failed",
                    finished_at=datetime.now(timezone.utc),
                    error=str(exc) or f"{operation_type} failed",
                )
            finally:
                self._queue.task_done()

    def _set_state(
        self,
        operation_id: str,
        state: CameraOperationState,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error: str | None = None,
        manual_state: CameraManualState | None = None,
    ) -> None:
        with self._lock:
            current = self._operations.get(operation_id)
            if not current:
                return
            self._operations[operation_id] = replace(
                current,
                state=state,
                started_at=started_at if started_at is not None else current.started_at,
                finished_at=finished_at if finished_at is not None else current.finished_at,
                error=error,
                manual_state=manual_state if manual_state is not None else current.manual_state,
            )
