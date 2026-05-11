from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class LightningSession:
    id: str
    profile_name: str
    commands: list[str]
    timeout_seconds: int
    active: bool = True
    run_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stopped_at: datetime | None = None
    script_state: str | None = None
    last_error: str | None = None

    @staticmethod
    def new(profile_name: str, commands: list[str], timeout_seconds: int) -> "LightningSession":
        return LightningSession(
            id=str(uuid4()),
            profile_name=profile_name,
            commands=commands,
            timeout_seconds=timeout_seconds,
            active=True,
            started_at=datetime.now(timezone.utc),
        )
