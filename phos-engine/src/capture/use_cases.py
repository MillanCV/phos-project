from __future__ import annotations

from src.camera.port import CameraGateway
from src.capture.domain import CaptureRecord
from src.capture.port import StorageGateway


class CapturePhoto:
    def __init__(self, camera_gateway: CameraGateway, storage_gateway: StorageGateway) -> None:
        self._camera_gateway = camera_gateway
        self._storage_gateway = storage_gateway

    def execute(self) -> CaptureRecord:
        output_path = self._camera_gateway.capture_photo()
        return self._storage_gateway.register_capture(output_path)


class GetLatestCapture:
    def __init__(self, storage_gateway: StorageGateway) -> None:
        self._storage_gateway = storage_gateway

    def execute(self) -> CaptureRecord | None:
        return self._storage_gateway.get_latest_capture()
