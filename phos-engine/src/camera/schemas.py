from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

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


class CameraManualCapabilitiesResponse(BaseModel):
    supports_flash_control: bool
    supports_focus_control: bool
    supports_zoom_control: bool
    supports_nd_filter: bool


class CameraZoomPositionResponse(BaseModel):
    step: int
    focal_length_mm: int
    focal_length_35mm_equiv_mm: int


class CameraManualStateResponse(BaseModel):
    power_state: Literal["active", "sleep", "deep_sleep", "waking", "error"]
    mode: Literal["record", "playback", "unknown"]
    shutter_seconds: float | None = None
    shutter_display: str
    iso: int | None = None
    aperture_display: str
    nd_enabled: bool | None = None
    zoom_step: int | None = None
    focus_mm: int | None = None
    flash_mode: int | None = None
    last_interaction_at: datetime
    idle_seconds: int
    capabilities: CameraManualCapabilitiesResponse
    exposure_control: Literal["auto", "manual", "unknown"] = "unknown"
    metering_shutter_display: str = "auto"
    metering_iso: int | None = None
    shutter_auto_active: bool = False
    iso_auto_active: bool = False
    focus_auto_active: bool = False
    zoom_focal_length_mm: int | None = None
    zoom_steps_count: int | None = None
    zoom_positions: list[CameraZoomPositionResponse] = Field(default_factory=list)
    focus_control: Literal["af", "mf", "unknown"] = "unknown"


IsoApplyValue = Union[Annotated[int, Field(ge=40, le=6400)], Literal["auto"], None]


class CameraManualApplyRequest(BaseModel):
    """exposure_mode=auto: P/AUTO + auto ISO. manual: switch to M (or Tv) then shutter/ISO so the body is in manual exposure, not P+override."""
    exposure_mode: Literal["auto", "manual"] = "manual"
    shutter_speed: str | None = None
    # Canon "real" ISO from get_iso_real() can be below 50 (e.g. 46) when synced from camera state.
    iso: IsoApplyValue = Field(default=None)
    nd_enabled: bool | None = None
    zoom_step: int | None = Field(default=None, ge=0)
    focus_mm: int | None = Field(default=None, ge=0)
    """Return to autofocus; skips set_focus / MF override."""
    focus_auto: bool = False
    flash_mode: int | None = None


class CameraPowerSleepRequest(BaseModel):
    level: Literal["sleep", "deep_sleep"] = "sleep"


class CameraOperationResponse(BaseModel):
    operation_id: str
    operation_type: str
    state: Literal["pending", "running", "completed", "failed"]
    submitted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    manual_state: CameraManualStateResponse | None = None
