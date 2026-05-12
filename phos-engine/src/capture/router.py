from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

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


@router.get("/latest/file")
async def latest_capture_file(container=Depends(get_container)) -> FileResponse:
    record = await run_in_threadpool(container.get_latest_capture.execute)
    if record is None:
        raise HTTPException(status_code=404, detail="no captures available")
    file_path = Path(record.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="latest capture file not found")
    return FileResponse(path=file_path, media_type="image/jpeg", filename=file_path.name)
