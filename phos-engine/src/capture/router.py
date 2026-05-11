from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from src.app.deps import get_container
from src.capture.schemas import CaptureResponse

router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.post("/photo", response_model=CaptureResponse)
async def capture_photo(container=Depends(get_container)) -> CaptureResponse:
    record = await run_in_threadpool(container.capture_photo.execute)
    return CaptureResponse(
        id=record.id,
        file_path=record.file_path,
        captured_at=record.captured_at,
        source=record.source,
    )


@router.get("/latest", response_model=CaptureResponse | None)
async def latest_capture(container=Depends(get_container)) -> CaptureResponse | None:
    record = await run_in_threadpool(container.get_latest_capture.execute)
    if record is None:
        return None
    return CaptureResponse(
        id=record.id,
        file_path=record.file_path,
        captured_at=record.captured_at,
        source=record.source,
    )
