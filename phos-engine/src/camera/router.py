from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app.deps import get_container
from src.camera.schemas import CameraStatusResponse

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/status", response_model=CameraStatusResponse)
def camera_status(container=Depends(get_container)) -> CameraStatusResponse:
    status = container.get_camera_status.execute()
    return CameraStatusResponse(
        connection=status.connection,
        model=status.model,
        battery_percent=status.battery_percent,
        last_error=status.last_error,
        checked_at=status.checked_at,
    )
