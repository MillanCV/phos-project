from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger("phos.camera.liveview.feed")


class LiveViewFeed:
    """Single producer at a fixed FPS; consumers read the latest JPEG without touching CHDK."""

    def __init__(self, capture_fn: Callable[[], bytes], fps: float = 5.0) -> None:
        self._capture = capture_fn
        self._interval = max(0.05, 1.0 / fps)
        self._frame_lock = threading.Lock()
        self._latest: bytes | None = None
        self._subscribers = 0
        self._sub_lock = threading.Lock()
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

    @property
    def interval_seconds(self) -> float:
        return self._interval

    def subscribe(self) -> None:
        with self._sub_lock:
            self._subscribers += 1
            if self._subscribers == 1:
                self._start_worker()

    def unsubscribe(self) -> None:
        with self._sub_lock:
            self._subscribers = max(0, self._subscribers - 1)
            if self._subscribers == 0:
                self._stop_worker()

    def get_latest(self) -> bytes | None:
        with self._frame_lock:
            return self._latest

    def _start_worker(self) -> None:
        self._stop.clear()
        self._worker = threading.Thread(target=self._run, name="liveview-feed", daemon=True)
        self._worker.start()

    def _stop_worker(self) -> None:
        self._stop.set()
        if self._worker is not None:
            self._worker.join(timeout=10.0)
            self._worker = None
        with self._frame_lock:
            self._latest = None

    def _run(self) -> None:
        consecutive_errors = 0
        while not self._stop.is_set():
            with self._sub_lock:
                if self._subscribers <= 0:
                    break
            try:
                frame = self._capture()
                consecutive_errors = 0
                if frame:
                    with self._frame_lock:
                        self._latest = frame
            except Exception:
                consecutive_errors += 1
                logger.warning("liveview feed capture failed", exc_info=True)
                if consecutive_errors >= 20:
                    time.sleep(1.0)
                    consecutive_errors = 0
                else:
                    time.sleep(min(0.5, self._interval))
                continue
            time.sleep(self._interval)
