from __future__ import annotations

from collections.abc import Callable
from threading import Event, Thread


class ThreadSchedulerGateway:
    def __init__(self) -> None:
        self._jobs: dict[str, Event] = {}

    def schedule_repeating(self, job_id: str, interval_seconds: int, callback: Callable[[], None]) -> None:
        self.cancel(job_id)
        stop_event = Event()
        self._jobs[job_id] = stop_event

        def runner() -> None:
            while not stop_event.wait(interval_seconds):
                callback()

        thread = Thread(target=runner, daemon=True, name=f"timelapse-{job_id}")
        thread.start()

    def cancel(self, job_id: str) -> None:
        stop_event = self._jobs.pop(job_id, None)
        if stop_event:
            stop_event.set()
