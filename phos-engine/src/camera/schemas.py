from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


CameraConnection = Literal["connected", "disconnected", "error"]


class CameraStatusResponse(BaseModel):
    connection: CameraConnection
    model: str | None = None
    battery_percent: int | None = None
    last_error: str | None = None
    checked_at: datetime
