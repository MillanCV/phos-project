from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app.deps import get_container
from src.timelapse.domain import TimelapsePlan
from src.timelapse.schemas import TimelapsePlanCreateRequest, TimelapsePlanResponse

router = APIRouter(prefix="/api/timelapse", tags=["timelapse"])


def _to_response(plan: TimelapsePlan) -> TimelapsePlanResponse:
    return TimelapsePlanResponse(
        id=plan.id,
        interval_seconds=plan.interval_seconds,
        window_start_hour=plan.window_start_hour,
        window_end_hour=plan.window_end_hour,
        active=plan.active,
        last_capture_at=plan.last_capture_at.isoformat() if plan.last_capture_at else None,
    )


@router.post("/plans", response_model=TimelapsePlanResponse)
def create_plan(
    payload: TimelapsePlanCreateRequest,
    container=Depends(get_container),
) -> TimelapsePlanResponse:
    plan = container.timelapse_manager.create_plan(
        interval_seconds=payload.interval_seconds,
        window_start_hour=payload.window_start_hour,
        window_end_hour=payload.window_end_hour,
    )
    return _to_response(plan)


@router.post("/plans/{plan_id}/start", response_model=TimelapsePlanResponse)
def start_plan(plan_id: str, container=Depends(get_container)) -> TimelapsePlanResponse:
    return _to_response(container.timelapse_manager.start_plan(plan_id))


@router.post("/plans/{plan_id}/stop", response_model=TimelapsePlanResponse)
def stop_plan(plan_id: str, container=Depends(get_container)) -> TimelapsePlanResponse:
    return _to_response(container.timelapse_manager.stop_plan(plan_id))


@router.get("/plans/{plan_id}", response_model=TimelapsePlanResponse)
def get_plan(plan_id: str, container=Depends(get_container)) -> TimelapsePlanResponse:
    return _to_response(container.timelapse_manager.get_plan(plan_id))
