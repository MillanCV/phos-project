from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.camera.domain import (
    CameraManualSettings,
    CameraManualState,
    CameraMode,
    CameraOperation,
    CameraStatus,
    ScriptExecutionResult,
    ScriptProfile,
)


class CameraControlPort(Protocol):
    def get_status(self) -> CameraStatus: ...

    def switch_mode(self, mode: CameraMode) -> None: ...

    def capture_photo(self) -> Path: ...

    def capture_live_view_frame(self) -> bytes: ...


class CameraScriptPort(Protocol):
    def run_script(self, profile: ScriptProfile) -> ScriptExecutionResult: ...

    def stop_script(self, run_id: str) -> None: ...

    def get_script_status(self, run_id: str) -> ScriptExecutionResult | None: ...


class CameraTransferPort(Protocol):
    def download_file(self, remote_path: str, local_path: Path) -> Path: ...

    def list_files(self, remote_dir: str) -> list[str]: ...


class CameraManualPort(Protocol):
    def get_manual_state(self) -> CameraManualState: ...

    def apply_manual_settings(self, settings: CameraManualSettings) -> CameraManualState: ...

    def sleep(self, level: str) -> CameraManualState: ...

    def wake(self) -> CameraManualState: ...

    def touch(self) -> CameraManualState: ...


class CameraOperationPort(Protocol):
    def submit_apply_manual_settings(self, settings: CameraManualSettings) -> CameraOperation: ...

    def submit_sleep(self, level: str) -> CameraOperation: ...

    def submit_wake(self) -> CameraOperation: ...

    def get_operation(self, operation_id: str) -> CameraOperation | None: ...
