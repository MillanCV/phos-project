from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


CameraConnection = Literal["connected", "disconnected", "error"]
CameraMode = Literal["record", "playback", "unknown"]
ScriptRunState = Literal["running", "completed", "failed", "stopped"]
CameraSessionState = Literal["idle", "busy", "error", "unavailable"]


@dataclass(slots=True)
class CameraStatus:
    connection: CameraConnection
    model: str | None = None
    battery_percent: int | None = None
    mode: CameraMode = "unknown"
    chdkptp_available: bool = False
    camera_session_state: CameraSessionState = "unavailable"
    last_successful_command_at: datetime | None = None
    last_command_duration_ms: int | None = None
    last_error: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True, frozen=True)
class ScriptProfile:
    name: str
    commands: list[str]
    timeout_seconds: int = 120
    expected_artifacts: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ScriptExecutionResult:
    run_id: str
    profile_name: str
    state: ScriptRunState
    started_at: datetime
    finished_at: datetime | None
    stdout: str
    stderr: str
    exit_code: int | None
    artifacts: list[str] = field(default_factory=list)
