from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app.deps import get_container
from src.motion.domain import MotionSession
from src.motion.schemas import MotionSessionResponse, MotionStartRequest

router = APIRouter(prefix="/api/motion", tags=["motion"])


def _to_response(session: MotionSession) -> MotionSessionResponse:
    return MotionSessionResponse(
        id=session.id,
        profile_name=session.profile_name,
        commands=session.commands,
        timeout_seconds=session.timeout_seconds,
        active=session.active,
        run_id=session.run_id,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        script_state=session.script_state,
        last_error=session.last_error,
    )


@router.post("/sessions", response_model=MotionSessionResponse)
def start_motion(payload: MotionStartRequest, container=Depends(get_container)) -> MotionSessionResponse:
    session = container.motion_manager.start_session(
        profile_name=payload.profile_name,
        commands=payload.commands,
        timeout_seconds=payload.timeout_seconds,
    )
    return _to_response(session)


@router.post("/sessions/{session_id}/stop", response_model=MotionSessionResponse)
def stop_motion(session_id: str, container=Depends(get_container)) -> MotionSessionResponse:
    session = container.motion_manager.stop_session(session_id)
    return _to_response(session)


@router.get("/sessions/{session_id}", response_model=MotionSessionResponse)
def get_motion(session_id: str, container=Depends(get_container)) -> MotionSessionResponse:
    session = container.motion_manager.get_session(session_id)
    return _to_response(session)
