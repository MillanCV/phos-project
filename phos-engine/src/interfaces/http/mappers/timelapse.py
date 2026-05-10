from __future__ import annotations

from src.interfaces.http.schemas.timelapse import TimelapsePlanResponse


def to_plan_response(plan) -> TimelapsePlanResponse:
    return TimelapsePlanResponse(
        id=plan.id,
        interval_seconds=plan.interval_seconds,
        window_start_hour=plan.window_start_hour,
        window_end_hour=plan.window_end_hour,
        active=plan.active,
        last_capture_at=plan.last_capture_at.isoformat() if plan.last_capture_at else None,
    )
