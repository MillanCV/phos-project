from __future__ import annotations

from pathlib import Path

from src.camera.domain import CameraStatus
from src.camera.use_cases import GetCameraStatus
from src.capture.domain import CaptureRecord, capture_record_from_path
from src.capture.use_cases import CapturePhoto, GetLatestCapture


class FakeCameraGateway:
    def __init__(self) -> None:
        self.status = CameraStatus(connection="connected", model="mock")
        self.capture_path = Path("/tmp/mock.jpg")

    def get_status(self) -> CameraStatus:
        return self.status

    def capture_photo(self) -> Path:
        return self.capture_path


class FakeStorageGateway:
    def __init__(self) -> None:
        self.latest: CaptureRecord | None = None

    def register_capture(self, file_path: Path, source: str = "camera") -> CaptureRecord:
        self.latest = capture_record_from_path(file_path, source=source)
        return self.latest

    def get_latest_capture(self) -> CaptureRecord | None:
        return self.latest


def test_get_camera_status_returns_gateway_value():
    gateway = FakeCameraGateway()
    use_case = GetCameraStatus(gateway)
    result = use_case.execute()
    assert result.connection == "connected"
    assert result.model == "mock"


def test_capture_photo_registers_record():
    camera = FakeCameraGateway()
    storage = FakeStorageGateway()
    use_case = CapturePhoto(camera, storage)

    result = use_case.execute()

    assert result.file_path == "/tmp/mock.jpg"
    assert storage.get_latest_capture() is not None


def test_get_latest_capture_when_empty_returns_none():
    storage = FakeStorageGateway()
    use_case = GetLatestCapture(storage)
    assert use_case.execute() is None
