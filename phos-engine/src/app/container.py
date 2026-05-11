from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from zoneinfo import ZoneInfo

from src.camera.gateway import ChdkptpCameraGateway
from src.camera.use_cases import GetCameraScriptStatus, GetCameraStatus, RunCameraScript, StopCameraScript
from src.capture.gateway import LocalStorageGateway
from src.capture.use_cases import CapturePhoto, GetLatestCapture
from src.lightning.manager import LightningManager
from src.lightning.repository import JsonLightningSessionRepository
from src.shared.logging import get_logger
from src.motion.manager import MotionManager
from src.motion.repository import JsonMotionSessionRepository
from src.solar.domain import SolarLocation
from src.solar.gateway import AstralSolarGateway
from src.solar.use_cases import GetSolarRange, GetSolarWindow
from src.system.gateway import HostMetricsGateway
from src.system.use_cases import GetSystemMetrics
from src.timelapse.manager import TimelapseManager
from src.timelapse.repository import JsonTimelapsePlanRepository
from src.timelapse.scheduler import ThreadSchedulerGateway


@dataclass(slots=True)
class ApiContainer:
    get_camera_status: GetCameraStatus
    run_camera_script: RunCameraScript
    stop_camera_script: StopCameraScript
    get_camera_script_status: GetCameraScriptStatus
    capture_photo: CapturePhoto
    get_latest_capture: GetLatestCapture
    get_system_metrics: GetSystemMetrics
    get_solar_window: GetSolarWindow
    get_solar_range: GetSolarRange
    timelapse_manager: TimelapseManager
    lightning_manager: LightningManager
    motion_manager: MotionManager
    local_tz: ZoneInfo
    logger: object


def build_container() -> ApiContainer:
    data_dir = Path(os.getenv("PHOS_DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
    captures_dir = data_dir / "captures"
    metadata_file = data_dir / "captures.json"
    plans_file = data_dir / "timelapse_plans.json"
    lightning_sessions_file = data_dir / "lightning_sessions.json"
    motion_sessions_file = data_dir / "motion_sessions.json"
    solar_cache_file = data_dir / "solar_cache.json"

    camera_gateway = ChdkptpCameraGateway(captures_dir=captures_dir)
    storage_gateway = LocalStorageGateway(metadata_file=metadata_file)
    scheduler_gateway = ThreadSchedulerGateway()
    plan_repository = JsonTimelapsePlanRepository(storage_file=plans_file)
    lightning_repository = JsonLightningSessionRepository(storage_file=lightning_sessions_file)
    motion_repository = JsonMotionSessionRepository(storage_file=motion_sessions_file)
    metrics_gateway = HostMetricsGateway(disk_path=Path("/"))
    solar_location = SolarLocation(
        latitude=float(os.getenv("PHOS_LATITUDE", "40.4168")),
        longitude=float(os.getenv("PHOS_LONGITUDE", "-3.7038")),
        timezone_name=os.getenv("PHOS_TIMEZONE", "Europe/Madrid"),
        name=os.getenv("PHOS_LOCATION_NAME", "Phos Site"),
    )
    solar_gateway = AstralSolarGateway(location=solar_location, cache_file=solar_cache_file)
    solar_gateway.prime_cache(days=int(os.getenv("PHOS_SOLAR_CACHE_DAYS", "30")))
    local_tz = ZoneInfo(solar_location.timezone_name)

    timelapse_manager = TimelapseManager(
        camera_gateway=camera_gateway,
        storage_gateway=storage_gateway,
        scheduler_gateway=scheduler_gateway,
        plan_repository=plan_repository,
    )
    timelapse_manager.bootstrap_active_plans()
    lightning_manager = LightningManager(
        script_runner=RunCameraScript(camera_gateway),
        script_stopper=StopCameraScript(camera_gateway),
        script_status=GetCameraScriptStatus(camera_gateway),
        repository=lightning_repository,
    )
    motion_manager = MotionManager(
        script_runner=RunCameraScript(camera_gateway),
        script_stopper=StopCameraScript(camera_gateway),
        script_status=GetCameraScriptStatus(camera_gateway),
        repository=motion_repository,
    )

    return ApiContainer(
        get_camera_status=GetCameraStatus(camera_gateway),
        run_camera_script=RunCameraScript(camera_gateway),
        stop_camera_script=StopCameraScript(camera_gateway),
        get_camera_script_status=GetCameraScriptStatus(camera_gateway),
        capture_photo=CapturePhoto(camera_gateway, storage_gateway),
        get_latest_capture=GetLatestCapture(storage_gateway),
        get_system_metrics=GetSystemMetrics(metrics_gateway),
        get_solar_window=GetSolarWindow(solar_gateway),
        get_solar_range=GetSolarRange(solar_gateway),
        timelapse_manager=timelapse_manager,
        lightning_manager=lightning_manager,
        motion_manager=motion_manager,
        local_tz=local_tz,
        logger=get_logger("phos.api"),
    )
