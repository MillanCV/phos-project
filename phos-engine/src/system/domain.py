from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class SystemMetrics:
    disk_free_bytes: int
    disk_total_bytes: int
    cpu_load_1m: float
    temperature_c: float | None
    uptime_seconds: float
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
