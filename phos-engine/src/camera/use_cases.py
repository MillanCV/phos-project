from __future__ import annotations

from pathlib import Path

from src.camera.domain import CameraStatus, ScriptExecutionResult, ScriptProfile
from src.camera.port import CameraGateway, CameraScriptPort


class GetCameraStatus:
    def __init__(self, camera_gateway: CameraGateway) -> None:
        self._camera_gateway = camera_gateway

    def execute(self) -> CameraStatus:
        return self._camera_gateway.get_status()


class CaptureSinglePhoto:
    def __init__(self, camera_gateway: CameraGateway) -> None:
        self._camera_gateway = camera_gateway

    def execute(self) -> Path:
        return self._camera_gateway.capture_photo()


class RunCameraScript:
    def __init__(self, script_port: CameraScriptPort) -> None:
        self._script_port = script_port

    def execute(self, profile: ScriptProfile) -> ScriptExecutionResult:
        return self._script_port.run_script(profile)


class StopCameraScript:
    def __init__(self, script_port: CameraScriptPort) -> None:
        self._script_port = script_port

    def execute(self, run_id: str) -> None:
        self._script_port.stop_script(run_id)


class GetCameraScriptStatus:
    def __init__(self, script_port: CameraScriptPort) -> None:
        self._script_port = script_port

    def execute(self, run_id: str) -> ScriptExecutionResult | None:
        return self._script_port.get_script_status(run_id)
