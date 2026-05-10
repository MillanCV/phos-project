from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.app.deps import get_container
from src.solar.mappers import to_solar_response, to_solar_summary
from src.solar.schemas import SolarRangeSummaryResponse, SolarWindowResponse

router = APIRouter(prefix="/api/solar", tags=["solar"])


@router.get("/today", response_model=SolarWindowResponse)
def solar_today(container=Depends(get_container)) -> SolarWindowResponse:
    today = datetime.now(container.local_tz).date()
    return to_solar_response(container.get_solar_window.execute(today))


@router.get("/range", response_model=list[SolarWindowResponse])
def solar_range(
    days: int = Query(default=7, ge=1, le=366),
    container=Depends(get_container),
) -> list[SolarWindowResponse]:
    today = datetime.now(container.local_tz).date()
    windows = container.get_solar_range.execute(start_date=today, days=days)
    return [to_solar_response(window) for window in windows]


@router.get("/range/summary", response_model=SolarRangeSummaryResponse)
def solar_range_summary(
    days: int = Query(default=30, ge=1, le=366),
    container=Depends(get_container),
) -> SolarRangeSummaryResponse:
    today = datetime.now(container.local_tz).date()
    windows = container.get_solar_range.execute(start_date=today, days=days)
    return to_solar_summary(windows)
