from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


CameraConnection = Literal["connected", "disconnected", "error"]
CameraMode = Literal["record", "playback", "unknown"]
ScriptRunState = Literal["running", "completed", "failed", "stopped"]
CameraSessionState = Literal["idle", "busy", "error", "unavailable"]
CameraPowerState = Literal["active", "sleep", "deep_sleep", "waking", "error"]


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


@dataclass(slots=True, frozen=True)
class CameraManualCapabilities:
    supports_flash_control: bool = True
    supports_focus_control: bool = True
    supports_zoom_control: bool = True
    supports_nd_filter: bool = True


@dataclass(slots=True, frozen=True)
class CameraZoomPosition:
    """One discrete zoom index with real focal length and a 35mm-equivalent label (crop factor from env)."""

    step: int
    focal_length_mm: int
    focal_length_35mm_equiv_mm: int


@dataclass(slots=True, frozen=True)
class CameraManualSettings:
    """When exposure_auto is True, CHDK switches back to automatic exposure (see gateway)."""
    exposure_auto: bool = False
    shutter_seconds: float | None = None
    """If True (manual exposure), do not override shutter speed on the body."""
    shutter_auto: bool = False
    iso: int | None = None
    """If True (manual exposure), enable auto ISO (set_iso_mode(0)) instead of a fixed value."""
    iso_auto: bool = False
    nd_enabled: bool | None = None
    zoom_step: int | None = None
    focus_mm: int | None = None
    """If True, return to AF (set_mf(0), set_aflock(0)) and skip set_focus."""
    focus_auto: bool = False
    flash_mode: int | None = None


CameraExposureControl = Literal["auto", "manual", "unknown"]


@dataclass(slots=True, frozen=True)
class CameraManualState:
    power_state: CameraPowerState
    mode: CameraMode
    shutter_seconds: float | None
    shutter_display: str
    iso: int | None
    aperture_display: str
    nd_enabled: bool | None
    zoom_step: int | None
    focus_mm: int | None
    flash_mode: int | None
    last_interaction_at: datetime
    idle_seconds: int
    capabilities: CameraManualCapabilities = field(default_factory=CameraManualCapabilities)
    """Last successful manual/apply exposure_mode; drives UI copy for AE vs manual."""
    exposure_control: CameraExposureControl = "unknown"
    """Live CHDK read (scene / preview); not guaranteed to match the next shot in P/AUTO."""
    metering_shutter_display: str = "auto"
    metering_iso: int | None = None
    """When exposure is manual, last apply left shutter to camera (no USB Tv override)."""
    shutter_auto_active: bool = False
    """When exposure is manual, last apply left ISO to auto (set_iso_mode(0))."""
    iso_auto_active: bool = False
    """When exposure is manual, last apply used focus_auto (AF); UI should show Auto, not live get_focus()."""
    focus_auto_active: bool = False
    """CHDK get_focal_length() at current zoom (lens mm), when available."""
    zoom_focal_length_mm: int | None = None
    """Number of zoom steps (indices 0 .. count-1). From get_zoom_steps()."""
    zoom_steps_count: int | None = None
    """Measured once per session: each step with real focal length and 35mm-equivalent label."""
    zoom_positions: tuple[CameraZoomPosition, ...] = ()
    """CHDK get_focus_mode(): AF vs MF when readable."""
    focus_control: Literal["af", "mf", "unknown"] = "unknown"


CameraOperationState = Literal["pending", "running", "completed", "failed"]


@dataclass(slots=True, frozen=True)
class CameraOperation:
    operation_id: str
    operation_type: str
    state: CameraOperationState
    submitted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    manual_state: CameraManualState | None = None
