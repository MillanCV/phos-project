from __future__ import annotations

from pathlib import Path

from src.camera.domain import CameraManualSettings, CameraManualState, CameraOperation, CameraStatus, ScriptExecutionResult, ScriptProfile
from src.camera.manual_service import CameraControlService
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


class CaptureLiveViewFrame:
    def __init__(self, camera_gateway: CameraGateway) -> None:
        self._camera_gateway = camera_gateway

    def execute(self) -> bytes:
        return self._camera_gateway.capture_live_view_frame()


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


class GetCameraManualState:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self) -> CameraManualState:
        return self._control_service.get_manual_state()


class TouchCameraControl:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self) -> CameraManualState:
        return self._control_service.touch()


class SubmitManualSettings:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self, settings: CameraManualSettings) -> CameraOperation:
        return self._control_service.submit_apply_manual_settings(settings)


class SubmitCameraSleep:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self, level: str) -> CameraOperation:
        return self._control_service.submit_sleep(level)


class SubmitCameraWake:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self) -> CameraOperation:
        return self._control_service.submit_wake()


class GetCameraOperationStatus:
    def __init__(self, control_service: CameraControlService) -> None:
        self._control_service = control_service

    def execute(self, operation_id: str) -> CameraOperation:
        return self._control_service.get_operation_required(operation_id)
