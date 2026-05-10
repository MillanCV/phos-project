from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends

from src.interfaces.http.container import ApiContainer
from src.interfaces.http.routers.deps import get_container

router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.post("/photo")
def capture(container: ApiContainer = Depends(get_container)) -> dict[str, Any]:
    return asdict(container.capture_photo.execute())


@router.get("/latest")
def latest_capture(container: ApiContainer = Depends(get_container)) -> dict[str, Any] | None:
    result = container.get_latest_capture.execute()
    return asdict(result) if result else None
