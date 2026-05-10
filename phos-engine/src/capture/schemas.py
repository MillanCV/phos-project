from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CaptureResponse(BaseModel):
    id: str
    file_path: str
    captured_at: datetime
    source: str
