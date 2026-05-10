from __future__ import annotations

from fastapi import APIRouter, Depends

from src.interfaces.http.container import ApiContainer
from src.interfaces.http.mappers.timelapse import to_plan_response
from src.interfaces.http.routers.deps import get_container
from src.interfaces.http.schemas.timelapse import TimelapsePlanCreateRequest, TimelapsePlanResponse

router = APIRouter(prefix="/api/timelapse", tags=["timelapse"])


@router.post("/plans", response_model=TimelapsePlanResponse)
def create_plan(
    payload: TimelapsePlanCreateRequest,
    container: ApiContainer = Depends(get_container),
) -> TimelapsePlanResponse:
    plan = container.timelapse_manager.create_plan(
        interval_seconds=payload.interval_seconds,
        window_start_hour=payload.window_start_hour,
        window_end_hour=payload.window_end_hour,
    )
    return to_plan_response(plan)


@router.post("/plans/{plan_id}/start", response_model=TimelapsePlanResponse)
def start_plan(plan_id: str, container: ApiContainer = Depends(get_container)) -> TimelapsePlanResponse:
    return to_plan_response(container.timelapse_manager.start_plan(plan_id))


@router.post("/plans/{plan_id}/stop", response_model=TimelapsePlanResponse)
def stop_plan(plan_id: str, container: ApiContainer = Depends(get_container)) -> TimelapsePlanResponse:
    return to_plan_response(container.timelapse_manager.stop_plan(plan_id))


@router.get("/plans/{plan_id}", response_model=TimelapsePlanResponse)
def get_plan(plan_id: str, container: ApiContainer = Depends(get_container)) -> TimelapsePlanResponse:
    return to_plan_response(container.timelapse_manager.get_plan(plan_id))
