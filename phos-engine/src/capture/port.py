from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.capture.domain import CaptureRecord


class StorageGateway(Protocol):
    def register_capture(self, file_path: Path, source: str = "camera") -> CaptureRecord: ...

    def get_latest_capture(self) -> CaptureRecord | None: ...
