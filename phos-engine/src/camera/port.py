from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.camera.domain import CameraStatus


class CameraGateway(Protocol):
    def get_status(self) -> CameraStatus: ...

    def capture_photo(self) -> Path: ...
