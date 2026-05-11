from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.camera.domain import CameraMode, CameraStatus, ScriptExecutionResult, ScriptProfile


class CameraControlPort(Protocol):
    def get_status(self) -> CameraStatus: ...

    def switch_mode(self, mode: CameraMode) -> None: ...

    def capture_photo(self) -> Path: ...


class CameraScriptPort(Protocol):
    def run_script(self, profile: ScriptProfile) -> ScriptExecutionResult: ...

    def stop_script(self, run_id: str) -> None: ...

    def get_script_status(self, run_id: str) -> ScriptExecutionResult | None: ...


class CameraTransferPort(Protocol):
    def download_file(self, remote_path: str, local_path: Path) -> Path: ...

    def list_files(self, remote_dir: str) -> list[str]: ...
