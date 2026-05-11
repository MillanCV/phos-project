from __future__ import annotations

from fastapi import APIRouter, Depends

from src.app.deps import get_container
from src.lightning.domain import LightningSession
from src.lightning.schemas import LightningSessionResponse, LightningStartRequest

router = APIRouter(prefix="/api/lightning", tags=["lightning"])


def _to_response(session: LightningSession) -> LightningSessionResponse:
    return LightningSessionResponse(
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


@router.post("/sessions", response_model=LightningSessionResponse)
def start_lightning(payload: LightningStartRequest, container=Depends(get_container)) -> LightningSessionResponse:
    session = container.lightning_manager.start_session(
        profile_name=payload.profile_name,
        commands=payload.commands,
        timeout_seconds=payload.timeout_seconds,
    )
    return _to_response(session)


@router.post("/sessions/{session_id}/stop", response_model=LightningSessionResponse)
def stop_lightning(session_id: str, container=Depends(get_container)) -> LightningSessionResponse:
    session = container.lightning_manager.stop_session(session_id)
    return _to_response(session)


@router.get("/sessions/{session_id}", response_model=LightningSessionResponse)
def get_lightning(session_id: str, container=Depends(get_container)) -> LightningSessionResponse:
    session = container.lightning_manager.get_session(session_id)
    return _to_response(session)
