from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from src.lightning.domain import LightningSession


class JsonLightningSessionRepository:
    def __init__(self, storage_file: Path) -> None:
        self._storage_file = storage_file
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)

    def save(self, session: LightningSession) -> LightningSession:
        items = {item.id: item for item in self.list_all()}
        items[session.id] = session
        payload = [self._serialize(item) for item in items.values()]
        self._storage_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return session

    def get(self, session_id: str) -> LightningSession | None:
        for item in self.list_all():
            if item.id == session_id:
                return item
        return None

    def list_all(self) -> list[LightningSession]:
        if not self._storage_file.exists():
            return []
        try:
            payload = json.loads(self._storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        sessions: list[LightningSession] = []
        for item in payload:
            if isinstance(item, dict):
                sessions.append(self._deserialize(item))
        return sessions

    @staticmethod
    def _serialize(session: LightningSession) -> dict[str, object]:
        return {
            "id": session.id,
            "profile_name": session.profile_name,
            "commands": session.commands,
            "timeout_seconds": session.timeout_seconds,
            "active": session.active,
            "run_id": session.run_id,
            "started_at": session.started_at.isoformat(),
            "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
            "script_state": session.script_state,
            "last_error": session.last_error,
        }

    @staticmethod
    def _deserialize(item: dict[str, object]) -> LightningSession:
        stopped_at = item.get("stopped_at")
        return LightningSession(
            id=str(item["id"]),
            profile_name=str(item["profile_name"]),
            commands=[str(cmd) for cmd in item.get("commands", [])],
            timeout_seconds=int(item.get("timeout_seconds", 120)),
            active=bool(item.get("active", True)),
            run_id=str(item["run_id"]) if item.get("run_id") else None,
            started_at=datetime.fromisoformat(str(item["started_at"])),
            stopped_at=datetime.fromisoformat(str(stopped_at)) if isinstance(stopped_at, str) else None,
            script_state=str(item["script_state"]) if item.get("script_state") else None,
            last_error=str(item["last_error"]) if item.get("last_error") else None,
        )
