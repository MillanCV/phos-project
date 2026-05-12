from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.app.deps import get_container
from src.camera.domain import ScriptProfile
from src.camera.presets import get_preset, list_presets
from src.camera.schemas import CameraPresetResponse, CameraStatusResponse, ScriptRunRequest, ScriptRunResponse

router = APIRouter(prefix="/api/camera", tags=["camera"])


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
