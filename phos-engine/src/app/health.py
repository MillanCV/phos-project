from __future__ import annotations

from datetime import datetime, timezone
import socket

from fastapi import APIRouter
from pydantic import BaseModel


class StatusResponse(BaseModel):
    message: str
    hostname: str
    timestamp_utc: str


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(
        message="Phos backend activo",
        hostname=socket.gethostname(),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
