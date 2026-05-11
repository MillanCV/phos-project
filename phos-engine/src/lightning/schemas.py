from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LightningStartRequest(BaseModel):
    profile_name: str = Field(default="lightning-default", min_length=1)
    commands: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class LightningSessionResponse(BaseModel):
    id: str
    profile_name: str
    commands: list[str]
    timeout_seconds: int
    active: bool
    run_id: str | None
    started_at: datetime
    stopped_at: datetime | None
    script_state: str | None
    last_error: str | None
