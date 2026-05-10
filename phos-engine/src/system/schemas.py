from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SystemMetricsResponse(BaseModel):
    disk_free_bytes: int
    disk_total_bytes: int
    cpu_load_1m: float
    temperature_c: float | None
    uptime_seconds: float
    collected_at: datetime
