from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import asdict
import os
from pathlib import Path
import socket
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.application.timelapse_manager import TimelapseManager
from src.application.use_cases import CapturePhoto, GetCameraStatus, GetLatestCapture, GetSystemMetrics
from src.domain.errors import CameraUnavailableError, NotFoundError, ValidationError
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


def create_app() -> FastAPI:
    configure_logging()
    logger = get_logger("phos.api")

    data_dir = Path(__file__).resolve().parents[3] / "data"
    captures_dir = data_dir / "captures"
    metadata_file = data_dir / "captures.json"
    plans_file = data_dir / "timelapse_plans.json"

    camera_gateway = ChdkptpCameraGateway(captures_dir=captures_dir)
    storage_gateway = LocalStorageGateway(metadata_file=metadata_file)
    scheduler_gateway = ThreadSchedulerGateway()
    plan_repository = JsonTimelapsePlanRepository(storage_file=plans_file)
    metrics_gateway = HostMetricsGateway(disk_path=Path("/"))

    get_camera_status = GetCameraStatus(camera_gateway)
    capture_photo = CapturePhoto(camera_gateway, storage_gateway)
    get_latest_capture = GetLatestCapture(storage_gateway)
    get_system_metrics = GetSystemMetrics(metrics_gateway)
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
