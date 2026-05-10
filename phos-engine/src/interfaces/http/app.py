from __future__ import annotations

from datetime import date, datetime, timezone
from dataclasses import asdict
import os
from pathlib import Path
import socket
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.application.solar_use_cases import GetSolarRange, GetSolarWindow
from src.application.timelapse_manager import TimelapseManager
from src.application.use_cases import CapturePhoto, GetCameraStatus, GetLatestCapture, GetSystemMetrics
from src.domain.errors import CameraUnavailableError, NotFoundError, ValidationError
from src.domain.solar import SolarLocation
from src.infrastructure.astral_solar_gateway import AstralSolarGateway
from src.infrastructure.chdkptp_camera_gateway import ChdkptpCameraGateway
from src.infrastructure.host_metrics_gateway import HostMetricsGateway
from src.infrastructure.json_timelapse_plan_repository import JsonTimelapsePlanRepository
from src.infrastructure.local_storage_gateway import LocalStorageGateway
from src.infrastructure.logging import configure_logging, get_logger
from src.infrastructure.thread_scheduler_gateway import ThreadSchedulerGateway


class StatusResponse(BaseModel):
    message: str
    hostname: str
    timestamp_utc: str


class TimelapsePlanCreateRequest(BaseModel):
    interval_seconds: int = Field(ge=10, le=86400)
    window_start_hour: int = Field(ge=0, le=23)
    window_end_hour: int = Field(ge=0, le=23)


class TimelapsePlanResponse(BaseModel):
    id: str
    interval_seconds: int
    window_start_hour: int
    window_end_hour: int
    active: bool
    last_capture_at: str | None


class SolarWindowResponse(BaseModel):
    day: date
    astronomical_dawn: datetime | None
    nautical_dawn: datetime | None
    civil_dawn: datetime | None
    blue_hour_morning_start: datetime | None
    blue_hour_morning_end: datetime | None
    golden_hour_morning_start: datetime | None
    sunrise: datetime
    golden_hour_morning_end: datetime | None
    sunset: datetime
    golden_hour_evening_start: datetime | None
    golden_hour_evening_end: datetime | None
    blue_hour_evening_start: datetime | None
    blue_hour_evening_end: datetime | None
    civil_dusk: datetime | None
    nautical_dusk: datetime | None
    astronomical_dusk: datetime | None
    solar_noon: datetime
    daylight_hours: float
    night_hours: float
    calculated_at: datetime


class SolarRangeSummaryResponse(BaseModel):
    start_date: date
    end_date: date
    days: int
    sunrise_min: datetime
    sunrise_max: datetime
    sunset_min: datetime
    sunset_max: datetime
    daylight_min_hours: float
    daylight_max_hours: float
    daylight_avg_hours: float
    night_min_hours: float
    night_max_hours: float
    night_avg_hours: float


def create_app() -> FastAPI:
    configure_logging()
    logger = get_logger("phos.api")

    data_dir = Path(__file__).resolve().parents[3] / "data"
    captures_dir = data_dir / "captures"
    metadata_file = data_dir / "captures.json"
    plans_file = data_dir / "timelapse_plans.json"
    solar_cache_file = data_dir / "solar_cache.json"

    camera_gateway = ChdkptpCameraGateway(captures_dir=captures_dir)
    storage_gateway = LocalStorageGateway(metadata_file=metadata_file)
    scheduler_gateway = ThreadSchedulerGateway()
    plan_repository = JsonTimelapsePlanRepository(storage_file=plans_file)
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

    get_camera_status = GetCameraStatus(camera_gateway)
    capture_photo = CapturePhoto(camera_gateway, storage_gateway)
    get_latest_capture = GetLatestCapture(storage_gateway)
    get_system_metrics = GetSystemMetrics(metrics_gateway)
    get_solar_window = GetSolarWindow(solar_gateway)
    get_solar_range = GetSolarRange(solar_gateway)
    timelapse_manager = TimelapseManager(
        camera_gateway=camera_gateway,
        storage_gateway=storage_gateway,
        scheduler_gateway=scheduler_gateway,
        plan_repository=plan_repository,
    )
    timelapse_manager.bootstrap_active_plans()

    app = FastAPI(title="Phos Engine", version="0.1.0")

    allowed_origins = [origin.strip() for origin in os.getenv("PHOS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info("request completed", extra={"request_id": request_id, "path": request.url.path})
        return response

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/status", response_model=StatusResponse)
    def status() -> StatusResponse:
        return StatusResponse(
            message="Phos backend activo",
            hostname=socket.gethostname(),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

    @app.get("/api/camera/status")
    def camera_status() -> dict[str, Any]:
        return asdict(get_camera_status.execute())

    @app.post("/api/capture/photo")
    def capture() -> dict[str, Any]:
        try:
            return asdict(capture_photo.execute())
        except CameraUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/capture/latest")
    def latest_capture() -> dict[str, Any] | None:
        result = get_latest_capture.execute()
        return asdict(result) if result else None

    @app.post("/api/timelapse/plans", response_model=TimelapsePlanResponse)
    def create_plan(payload: TimelapsePlanCreateRequest) -> TimelapsePlanResponse:
        try:
            plan = timelapse_manager.create_plan(
                interval_seconds=payload.interval_seconds,
                window_start_hour=payload.window_start_hour,
                window_end_hour=payload.window_end_hour,
            )
            return _to_plan_response(plan)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/timelapse/plans/{plan_id}/start", response_model=TimelapsePlanResponse)
    def start_plan(plan_id: str) -> TimelapsePlanResponse:
        try:
            return _to_plan_response(timelapse_manager.start_plan(plan_id))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/timelapse/plans/{plan_id}/stop", response_model=TimelapsePlanResponse)
    def stop_plan(plan_id: str) -> TimelapsePlanResponse:
        try:
            return _to_plan_response(timelapse_manager.stop_plan(plan_id))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/timelapse/plans/{plan_id}", response_model=TimelapsePlanResponse)
    def get_plan(plan_id: str) -> TimelapsePlanResponse:
        try:
            return _to_plan_response(timelapse_manager.get_plan(plan_id))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/system/metrics")
    def system_metrics() -> dict[str, Any]:
        return asdict(get_system_metrics.execute())

    @app.get("/api/solar/today", response_model=SolarWindowResponse)
    def solar_today() -> SolarWindowResponse:
        today = datetime.now(local_tz).date()
        return _to_solar_response(get_solar_window.execute(today))

    @app.get("/api/solar/range", response_model=list[SolarWindowResponse])
    def solar_range(days: int = Query(default=7, ge=1, le=366)) -> list[SolarWindowResponse]:
        today = datetime.now(local_tz).date()
        windows = get_solar_range.execute(start_date=today, days=days)
        return [_to_solar_response(window) for window in windows]

    @app.get("/api/solar/range/summary", response_model=SolarRangeSummaryResponse)
    def solar_range_summary(days: int = Query(default=30, ge=1, le=366)) -> SolarRangeSummaryResponse:
        today = datetime.now(local_tz).date()
        windows = get_solar_range.execute(start_date=today, days=days)
        return _to_solar_summary(windows)

    return app


def _to_plan_response(plan) -> TimelapsePlanResponse:
    return TimelapsePlanResponse(
        id=plan.id,
        interval_seconds=plan.interval_seconds,
        window_start_hour=plan.window_start_hour,
        window_end_hour=plan.window_end_hour,
        active=plan.active,
        last_capture_at=plan.last_capture_at.isoformat() if plan.last_capture_at else None,
    )


def _to_solar_response(window) -> SolarWindowResponse:
    return SolarWindowResponse(
        day=window.day,
        astronomical_dawn=window.astronomical_dawn,
        nautical_dawn=window.nautical_dawn,
        civil_dawn=window.civil_dawn,
        blue_hour_morning_start=window.blue_hour_morning_start,
        blue_hour_morning_end=window.blue_hour_morning_end,
        golden_hour_morning_start=window.golden_hour_morning_start,
        sunrise=window.sunrise,
        golden_hour_morning_end=window.golden_hour_morning_end,
        sunset=window.sunset,
        golden_hour_evening_start=window.golden_hour_evening_start,
        golden_hour_evening_end=window.golden_hour_evening_end,
        blue_hour_evening_start=window.blue_hour_evening_start,
        blue_hour_evening_end=window.blue_hour_evening_end,
        civil_dusk=window.civil_dusk,
        nautical_dusk=window.nautical_dusk,
        astronomical_dusk=window.astronomical_dusk,
        solar_noon=window.solar_noon,
        daylight_hours=round(window.daylight_seconds / 3600, 3),
        night_hours=round(window.night_seconds / 3600, 3),
        calculated_at=window.calculated_at,
    )


def _to_solar_summary(windows) -> SolarRangeSummaryResponse:
    if not windows:
        raise HTTPException(status_code=404, detail="no solar windows available")

    daylight_hours = [window.daylight_seconds / 3600 for window in windows]
    night_hours = [window.night_seconds / 3600 for window in windows]
    return SolarRangeSummaryResponse(
        start_date=windows[0].day,
        end_date=windows[-1].day,
        days=len(windows),
        sunrise_min=min(window.sunrise for window in windows),
        sunrise_max=max(window.sunrise for window in windows),
        sunset_min=min(window.sunset for window in windows),
        sunset_max=max(window.sunset for window in windows),
        daylight_min_hours=round(min(daylight_hours), 3),
        daylight_max_hours=round(max(daylight_hours), 3),
        daylight_avg_hours=round(sum(daylight_hours) / len(daylight_hours), 3),
        night_min_hours=round(min(night_hours), 3),
        night_max_hours=round(max(night_hours), 3),
        night_avg_hours=round(sum(night_hours) / len(night_hours), 3),
    )
