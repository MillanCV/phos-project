from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


CameraConnection = Literal["connected", "disconnected", "error"]


@dataclass(slots=True)
class CameraStatus:
    connection: CameraConnection
    model: str | None = None
    battery_percent: int | None = None
    last_error: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
