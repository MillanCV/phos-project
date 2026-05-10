from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends

from src.interfaces.http.container import ApiContainer
from src.interfaces.http.routers.deps import get_container

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/metrics")
def system_metrics(container: ApiContainer = Depends(get_container)) -> dict[str, Any]:
    return asdict(container.get_system_metrics.execute())
