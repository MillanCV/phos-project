from __future__ import annotations

from src.camera.domain import CameraStatus
from src.camera.port import CameraGateway


class GetCameraStatus:
    def __init__(self, camera_gateway: CameraGateway) -> None:
        self._camera_gateway = camera_gateway

    def execute(self) -> CameraStatus:
        return self._camera_gateway.get_status()
