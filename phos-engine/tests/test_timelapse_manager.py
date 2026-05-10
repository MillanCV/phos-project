from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.timelapse.manager import TimelapseManager
from src.timelapse.repository import JsonTimelapsePlanRepository
from src.timelapse.scheduler import ThreadSchedulerGateway


class FakeCameraGateway:
    def __init__(self) -> None:
        self.captured = 0

    def get_status(self):
        raise NotImplementedError

    def capture_photo(self) -> Path:
        self.captured += 1
        return Path("/tmp/mock.jpg")


class FakeStorageGateway:
    def __init__(self) -> None:
        self.registered = 0

    def register_capture(self, file_path: Path, source: str = "camera"):
        self.registered += 1
        return {"path": str(file_path), "source": source}

    def get_latest_capture(self):
        return None


def test_create_plan_persists_to_repository():
    with TemporaryDirectory() as tmp_dir:
        repository = JsonTimelapsePlanRepository(Path(tmp_dir) / "plans.json")
        manager = TimelapseManager(
            camera_gateway=FakeCameraGateway(),
            storage_gateway=FakeStorageGateway(),
            scheduler_gateway=ThreadSchedulerGateway(),
            plan_repository=repository,
        )

        plan = manager.create_plan(interval_seconds=30, window_start_hour=0, window_end_hour=23)
        loaded = repository.get(plan.id)

        assert loaded is not None
        assert loaded.interval_seconds == 30
        assert not loaded.active
