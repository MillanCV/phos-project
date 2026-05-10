from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from src.system.domain import SystemMetrics


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
        proc_uptime = Path("/proc/uptime")
        if proc_uptime.exists():
            with proc_uptime.open(encoding="utf-8") as fp:
                uptime = float(fp.read().split()[0])
            return time.time() - uptime

        # macOS fallback: parse `kern.boottime`.
        try:
            output = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True).strip()
            match = re.search(r"sec\s*=\s*(\d+)", output)
            if match:
                return float(match.group(1))
        except (OSError, subprocess.CalledProcessError):
            pass

        # Last-resort fallback to avoid crashing metrics endpoint.
        return time.time()
