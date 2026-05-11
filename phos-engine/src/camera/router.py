from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.app.deps import get_container
from src.camera.domain import ScriptProfile
from src.camera.schemas import CameraStatusResponse, ScriptRunRequest, ScriptRunResponse

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/status", response_model=CameraStatusResponse)
async def camera_status(container=Depends(get_container)) -> CameraStatusResponse:
    status = await run_in_threadpool(container.get_camera_status.execute)
    return CameraStatusResponse(
        connection=status.connection,
        model=status.model,
        battery_percent=status.battery_percent,
        mode=status.mode,
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
