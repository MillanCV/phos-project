from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from src.camera.domain import ScriptProfile
from src.camera.use_cases import GetCameraScriptStatus, RunCameraScript, StopCameraScript
from src.lightning.domain import LightningSession
from src.shared.errors import NotFoundError, ValidationError


class LightningSessionRepository(Protocol):
    def save(self, session: LightningSession) -> LightningSession: ...

    def get(self, session_id: str) -> LightningSession | None: ...


class LightningManager:
    def __init__(
        self,
        script_runner: RunCameraScript,
        script_stopper: StopCameraScript,
        script_status: GetCameraScriptStatus,
        repository: LightningSessionRepository,
    ) -> None:
        self._script_runner = script_runner
        self._script_stopper = script_stopper
        self._script_status = script_status
        self._repository = repository

    def start_session(self, profile_name: str, commands: list[str], timeout_seconds: int = 300) -> LightningSession:
        if not commands:
            raise ValidationError("commands cannot be empty")
        if timeout_seconds <= 0:
            raise ValidationError("timeout_seconds must be > 0")

        session = LightningSession.new(
            profile_name=profile_name,
            commands=commands,
            timeout_seconds=timeout_seconds,
        )
        result = self._script_runner.execute(
            ScriptProfile(
                name=profile_name,
                commands=commands,
                timeout_seconds=timeout_seconds,
            )
        )
        session.run_id = result.run_id
        session.script_state = result.state
        session.active = result.state == "running"
        if result.state in ("completed", "failed", "stopped"):
            session.active = False
            session.stopped_at = result.finished_at or datetime.now(timezone.utc)
        return self._repository.save(session)

    def stop_session(self, session_id: str) -> LightningSession:
        session = self.get_session(session_id)
        if not session.run_id:
            session.active = False
            session.stopped_at = datetime.now(timezone.utc)
            return self._repository.save(session)
        self._script_stopper.execute(session.run_id)
        session.active = False
        session.script_state = "stopped"
        session.stopped_at = datetime.now(timezone.utc)
        return self._repository.save(session)

    def get_session(self, session_id: str) -> LightningSession:
        session = self._repository.get(session_id)
        if not session:
            raise NotFoundError(f"lightning session {session_id} not found")
        if session.run_id:
            status = self._script_status.execute(session.run_id)
            if status:
                session.script_state = status.state
                if status.state in ("completed", "failed", "stopped") and session.active:
                    session.active = False
                    session.stopped_at = status.finished_at or datetime.now(timezone.utc)
                self._repository.save(session)
        return session
