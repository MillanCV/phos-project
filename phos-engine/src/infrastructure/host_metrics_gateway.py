from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import time

from src.domain.models import SystemMetrics


class HostMetricsGateway:
    def __init__(self, disk_path: Path) -> None:
        self._disk_path = disk_path

    def get_metrics(self) -> SystemMetrics:
        usage = shutil.disk_usage(self._disk_path)
        cpu_load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
        return SystemMetrics(
            disk_free_bytes=usage.free,
            disk_total_bytes=usage.total,
            cpu_load_1m=cpu_load,
            temperature_c=self._read_cpu_temp(),
            uptime_seconds=time.time() - self._boot_time_epoch(),
            collected_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _read_cpu_temp() -> float | None:
        temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
        if not temp_file.exists():
            return None
        try:
            raw = temp_file.read_text(encoding="utf-8").strip()
            return round(int(raw) / 1000, 2)
        except (ValueError, OSError):
            return None

    @staticmethod
    def _boot_time_epoch() -> float:
        with Path("/proc/uptime").open(encoding="utf-8") as fp:
            uptime = float(fp.read().split()[0])
        return time.time() - uptime
