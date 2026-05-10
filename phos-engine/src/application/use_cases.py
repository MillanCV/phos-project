from __future__ import annotations

from src.application.ports import CameraGateway, MetricsGateway, StorageGateway
from src.domain.models import CameraStatus, CaptureRecord, SystemMetrics


class GetCameraStatus:
    def __init__(self, camera_gateway: CameraGateway) -> None:
        self._camera_gateway = camera_gateway

    def execute(self) -> CameraStatus:
        return self._camera_gateway.get_status()


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


class GetSystemMetrics:
    def __init__(self, metrics_gateway: MetricsGateway) -> None:
        self._metrics_gateway = metrics_gateway

    def execute(self) -> SystemMetrics:
        return self._metrics_gateway.get_metrics()
