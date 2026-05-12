from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CameraConnection = Literal["connected", "disconnected", "error"]


class CameraStatusResponse(BaseModel):
    connection: CameraConnection
    model: str | None = None
    battery_percent: int | None = None
    mode: Literal["record", "playback", "unknown"] = "unknown"
    chdkptp_available: bool = False
    camera_session_state: Literal["idle", "busy", "error", "unavailable"] = "unavailable"
    last_successful_command_at: datetime | None = None
    last_command_duration_ms: int | None = None
    last_error: str | None = None
    checked_at: datetime


class ScriptRunRequest(BaseModel):
    name: str = Field(min_length=1)
    commands: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=120, ge=1, le=3600)
    expected_artifacts: list[str] = Field(default_factory=list)


class ScriptRunResponse(BaseModel):
    run_id: str
    profile_name: str
    state: Literal["running", "completed", "failed", "stopped"]
    started_at: datetime
    finished_at: datetime | None
    stdout: str
    stderr: str
    exit_code: int | None
    artifacts: list[str]


class CameraPresetResponse(BaseModel):
    name: str
    description: str
    timeout_seconds: int
