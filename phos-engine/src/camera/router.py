from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse

from src.app.container import ApiContainer
from src.app.deps import get_container
from src.camera.domain import CameraManualSettings, CameraOperation, ScriptProfile
from src.camera.presets import get_preset, list_presets
from src.camera.schemas import (
    CameraManualApplyRequest,
    CameraManualCapabilitiesResponse,
    CameraManualStateResponse,
    CameraOperationResponse,
    CameraPowerSleepRequest,
    CameraPresetResponse,
    CameraStatusResponse,
    CameraZoomPositionResponse,
    ScriptRunRequest,
    ScriptRunResponse,
)
from src.shared.errors import ValidationError

router = APIRouter(prefix="/api/camera", tags=["camera"])


def _parse_shutter_speed(value: str) -> float:
    item = value.strip()
    if not item:
        raise ValidationError("shutter_speed cannot be empty")
    try:
        if item.endswith('"'):
            return float(item[:-1])
        if "/" in item:
            num, den = item.split("/", maxsplit=1)
            denominator = float(den)
            if denominator <= 0:
                raise ValidationError("shutter_speed denominator must be > 0")
            return float(num) / denominator
        return float(item)
    except ValueError as exc:
        raise ValidationError("invalid shutter_speed format") from exc


def _to_manual_state_response(state) -> CameraManualStateResponse:
    return CameraManualStateResponse(
        power_state=state.power_state,
        mode=state.mode,
        shutter_seconds=state.shutter_seconds,
        shutter_display=state.shutter_display,
        iso=state.iso,
        aperture_display=state.aperture_display,
        nd_enabled=state.nd_enabled,
        zoom_step=state.zoom_step,
        focus_mm=state.focus_mm,
        flash_mode=state.flash_mode,
        last_interaction_at=state.last_interaction_at,
        idle_seconds=state.idle_seconds,
        capabilities=CameraManualCapabilitiesResponse(
            supports_flash_control=state.capabilities.supports_flash_control,
            supports_focus_control=state.capabilities.supports_focus_control,
            supports_zoom_control=state.capabilities.supports_zoom_control,
            supports_nd_filter=state.capabilities.supports_nd_filter,
        ),
        exposure_control=state.exposure_control,
        metering_shutter_display=state.metering_shutter_display,
        metering_iso=state.metering_iso,
        shutter_auto_active=state.shutter_auto_active,
        iso_auto_active=state.iso_auto_active,
        focus_auto_active=state.focus_auto_active,
        zoom_focal_length_mm=state.zoom_focal_length_mm,
        zoom_steps_count=state.zoom_steps_count,
        zoom_positions=[
            CameraZoomPositionResponse(
                step=p.step,
                focal_length_mm=p.focal_length_mm,
                focal_length_35mm_equiv_mm=p.focal_length_35mm_equiv_mm,
            )
            for p in state.zoom_positions
        ],
        focus_control=state.focus_control,
    )


def _to_operation_response(operation: CameraOperation) -> CameraOperationResponse:
    return CameraOperationResponse(
        operation_id=operation.operation_id,
        operation_type=operation.operation_type,
        state=operation.state,
        submitted_at=operation.submitted_at,
        started_at=operation.started_at,
        finished_at=operation.finished_at,
        error=operation.error,
        manual_state=_to_manual_state_response(operation.manual_state) if operation.manual_state is not None else None,
    )


@router.get("/status", response_model=CameraStatusResponse)
async def camera_status(container=Depends(get_container)) -> CameraStatusResponse:
    status = await run_in_threadpool(container.get_camera_status.execute)
    return CameraStatusResponse(
        connection=status.connection,
        model=status.model,
        battery_percent=status.battery_percent,
        mode=status.mode,
        chdkptp_available=status.chdkptp_available,
        camera_session_state=status.camera_session_state,
        last_successful_command_at=status.last_successful_command_at,
        last_command_duration_ms=status.last_command_duration_ms,
        last_error=status.last_error,
        checked_at=status.checked_at,
    )


@router.post("/scripts/run", response_model=ScriptRunResponse)
async def run_script(payload: ScriptRunRequest, container=Depends(get_container)) -> ScriptRunResponse:
    profile = ScriptProfile(
        name=payload.name,
        commands=payload.commands,
        timeout_seconds=payload.timeout_seconds,
        expected_artifacts=payload.expected_artifacts,
    )
    result = await run_in_threadpool(
        container.run_camera_script.execute,
        profile,
    )
    return ScriptRunResponse(
        run_id=result.run_id,
        profile_name=result.profile_name,
        state=result.state,
        started_at=result.started_at,
        finished_at=result.finished_at,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        artifacts=result.artifacts,
    )


@router.get("/scripts/{run_id}", response_model=ScriptRunResponse)
async def script_status(run_id: str, container=Depends(get_container)) -> ScriptRunResponse:
    result = await run_in_threadpool(container.get_camera_script_status.execute, run_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"script run {run_id} not found")
    return ScriptRunResponse(
        run_id=result.run_id,
        profile_name=result.profile_name,
        state=result.state,
        started_at=result.started_at,
        finished_at=result.finished_at,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        artifacts=result.artifacts,
    )


@router.post("/scripts/{run_id}/stop")
async def stop_script(run_id: str, container=Depends(get_container)) -> dict[str, str]:
    await run_in_threadpool(container.stop_camera_script.execute, run_id)
    return {"status": "stopped", "run_id": run_id}


@router.get("/manual/state", response_model=CameraManualStateResponse)
async def camera_manual_state(container: ApiContainer = Depends(get_container)) -> CameraManualStateResponse:
    state = await run_in_threadpool(container.get_camera_manual_state.execute)
    return _to_manual_state_response(state)


@router.post("/manual/apply", response_model=CameraOperationResponse, status_code=status.HTTP_202_ACCEPTED)
async def apply_manual_settings(
    payload: CameraManualApplyRequest,
    container: ApiContainer = Depends(get_container),
) -> CameraOperationResponse:
    shutter_auto = False
    iso_auto = False
    shutter_seconds: float | None = None
    iso: int | None = None
    if payload.exposure_mode == "auto":
        shutter_seconds = None
        iso = None
    else:
        raw_shutter = (payload.shutter_speed or "").strip().lower()
        if raw_shutter == "auto":
            shutter_auto = True
        elif payload.shutter_speed is not None and payload.shutter_speed.strip():
            shutter_seconds = _parse_shutter_speed(payload.shutter_speed)
        if payload.iso == "auto":
            iso_auto = True
        elif payload.iso is not None:
            iso = int(payload.iso)
    operation = await run_in_threadpool(
        container.submit_manual_settings.execute,
        CameraManualSettings(
            exposure_auto=payload.exposure_mode == "auto",
            shutter_seconds=shutter_seconds,
            shutter_auto=shutter_auto,
            iso=iso,
            iso_auto=iso_auto,
            nd_enabled=payload.nd_enabled,
            zoom_step=payload.zoom_step,
            focus_mm=payload.focus_mm,
            focus_auto=payload.focus_auto,
            flash_mode=payload.flash_mode,
        ),
    )
    return _to_operation_response(operation)


@router.post("/power/sleep", response_model=CameraOperationResponse, status_code=status.HTTP_202_ACCEPTED)
async def camera_sleep(
    payload: CameraPowerSleepRequest,
    container: ApiContainer = Depends(get_container),
) -> CameraOperationResponse:
    operation = await run_in_threadpool(container.submit_camera_sleep.execute, payload.level)
    return _to_operation_response(operation)


@router.post("/power/wake", response_model=CameraOperationResponse, status_code=status.HTTP_202_ACCEPTED)
async def camera_wake(container: ApiContainer = Depends(get_container)) -> CameraOperationResponse:
    operation = await run_in_threadpool(container.submit_camera_wake.execute)
    return _to_operation_response(operation)


@router.post("/power/touch", response_model=CameraManualStateResponse)
async def camera_touch(container: ApiContainer = Depends(get_container)) -> CameraManualStateResponse:
    state = await run_in_threadpool(container.touch_camera_control.execute)
    return _to_manual_state_response(state)


@router.get("/liveview/frame")
async def camera_live_view_frame(container: ApiContainer = Depends(get_container)) -> Response:
    cached = container.live_view_feed.get_latest()
    if cached:
        return Response(content=cached, media_type="image/jpeg")
    frame = await run_in_threadpool(container.capture_live_view_frame.execute)
    return Response(content=frame, media_type="image/jpeg")


@router.get(
    "/liveview/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "MJPEG live stream",
            "content": {
                "multipart/x-mixed-replace": {},
            },
        }
    },
)
async def camera_live_view_stream(request: Request, container: ApiContainer = Depends(get_container)) -> StreamingResponse:
    feed = container.live_view_feed
    feed.subscribe()
    try:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            if feed.get_latest():
                break
            await asyncio.sleep(0.05)
        else:
            feed.unsubscribe()
            raise HTTPException(
                status_code=503,
                detail="live view unavailable: no frame within timeout (is the camera connected?)",
            )
    except HTTPException:
        raise
    except Exception as exc:
        feed.unsubscribe()
        raise HTTPException(status_code=503, detail=f"live view unavailable: {exc}") from exc

    interval = feed.interval_seconds

    async def _iter_frames():
        try:
            while not await request.is_disconnected():
                frame = feed.get_latest()
                if frame:
                    chunk = (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        + f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii")
                        + frame
                        + b"\r\n"
                    )
                    yield chunk
                await asyncio.sleep(interval)
        finally:
            feed.unsubscribe()

    return StreamingResponse(
        _iter_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@router.get("/operations/{operation_id}", response_model=CameraOperationResponse)
async def camera_operation(operation_id: str, container: ApiContainer = Depends(get_container)) -> CameraOperationResponse:
    operation = await run_in_threadpool(container.get_camera_operation_status.execute, operation_id)
    return _to_operation_response(operation)


@router.get("/presets", response_model=list[CameraPresetResponse])
async def camera_presets() -> list[CameraPresetResponse]:
    return [
        CameraPresetResponse(
            name=preset.name,
            description=preset.description,
            timeout_seconds=preset.timeout_seconds,
        )
        for preset in list_presets()
    ]


@router.post("/presets/{preset_name}/run", response_model=ScriptRunResponse)
async def run_preset(preset_name: str, container=Depends(get_container)) -> ScriptRunResponse:
    preset = get_preset(preset_name)
    result = await run_in_threadpool(
        container.run_camera_script.execute,
        ScriptProfile(
            name=preset.name,
            commands=preset.commands,
            timeout_seconds=preset.timeout_seconds,
        ),
    )
    return ScriptRunResponse(
        run_id=result.run_id,
        profile_name=result.profile_name,
        state=result.state,
        started_at=result.started_at,
        finished_at=result.finished_at,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        artifacts=result.artifacts,
    )
