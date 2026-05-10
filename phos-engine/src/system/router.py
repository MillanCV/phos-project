from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app.deps import get_container
from src.system.schemas import SystemMetricsResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/metrics", response_model=SystemMetricsResponse)
def system_metrics(container=Depends(get_container)) -> SystemMetricsResponse:
    metrics = container.get_system_metrics.execute()
    return SystemMetricsResponse(
        disk_free_bytes=metrics.disk_free_bytes,
        disk_total_bytes=metrics.disk_total_bytes,
        cpu_load_1m=metrics.cpu_load_1m,
        temperature_c=metrics.temperature_c,
        uptime_seconds=metrics.uptime_seconds,
        collected_at=metrics.collected_at,
    )
