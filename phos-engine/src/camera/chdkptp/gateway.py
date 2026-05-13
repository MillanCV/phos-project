from __future__ import annotations

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import re
import shutil
import time
from typing import Literal
from uuid import uuid4

from src.camera.chdkptp.output_parser import collect_artifacts, parse_script_state
from src.camera.chdkptp.session import ChdkptpSession
from src.camera.domain import (
    CameraManualCapabilities,
    CameraManualSettings,
    CameraManualState,
    CameraMode,
    CameraStatus,
    CameraZoomPosition,
    ScriptExecutionResult,
    ScriptProfile,
)
from src.shared.errors import CameraUnavailableError, NotFoundError, ValidationError


class ChdkptpCameraGateway:
    def __init__(self, captures_dir: Path) -> None:
        self._captures_dir = captures_dir
        self._captures_dir.mkdir(parents=True, exist_ok=True)
        self._chdkptp_bin = os.getenv("CHDKPTP_BIN", "chdkptp")
        self._mock_mode = os.getenv("PHOS_CAMERA_MOCK", "false").lower() == "true"
        self._session = ChdkptpSession(self._chdkptp_bin)
        self._script_runs: dict[str, ScriptExecutionResult] = {}
        self._camera_session_state: str = "unavailable"
        self._last_successful_command_at: datetime | None = None
        self._last_command_duration_ms: int | None = None
        self._manual_state_cache = CameraManualState(
            power_state="active",
            mode="record",
            shutter_seconds=None,
            shutter_display="auto",
            iso=None,
            aperture_display="auto",
            nd_enabled=None,
            zoom_step=None,
            focus_mm=None,
            flash_mode=None,
            last_interaction_at=datetime.now(timezone.utc),
            idle_seconds=0,
            capabilities=CameraManualCapabilities(),
            exposure_control="unknown",
            metering_shutter_display="auto",
            metering_iso=None,
        )
        # CHDK get_tv96/get_iso_real often lag metering vs overrides used at shoot; panel follows last USB apply.
        self._last_applied_manual_tv96: int | None = None
        self._last_applied_manual_iso: int | None = None
        self._last_applied_nd: bool | None = None
        # Last successful /camera/manual/apply exposure_mode: in "auto", do not show preview Tv/ISO as if they were shot values.
        self._exposure_ui_mode: str | None = None
        self._shutter_auto_active = False
        self._iso_auto_active = False
        self._focus_auto_active = False
        # CHDK requires sleep after set_focus before get_focus matches; zoom then focus needs settle time.
        self._focus_settle_ms = min(4000, max(400, int(os.getenv("PHOS_FOCUS_SETTLE_MS", "1500"))))
        self._focus_after_zoom_ms = min(2000, max(0, int(os.getenv("PHOS_FOCUS_AFTER_ZOOM_MS", "600"))))
        # Many IXUS/ELPH need AF lock before set_focus() bites; disable with PHOS_FOCUS_USE_AFLOCK=false if it hurts.
        self._focus_use_aflock = os.getenv("PHOS_FOCUS_USE_AFLOCK", "true").lower() == "true"
        # Multiply lens focal length (mm) to approximate 35mm full-frame equivalent for UI labels.
        self._focal_35mm_equiv_mult = float(os.getenv("PHOS_FOCAL_35MM_EQUIV_MULT", "5.64"))
        self._zoom_focal_by_step: list[int] | None = None
        self._capture_reassert_manual = os.getenv("PHOS_CAPTURE_REASSERT_MANUAL", "true").lower() == "true"
        self._liveview_reassert_manual = os.getenv("PHOS_LIVEVIEW_REASSERT_MANUAL", "false").lower() == "true"

    def get_status(self) -> CameraStatus:
        if self._mock_mode:
            return CameraStatus(
                connection="connected",
                model="Canon IXUS 105 (mock)",
                battery_percent=100,
                mode="record",
                chdkptp_available=True,
                camera_session_state="idle",
                last_successful_command_at=datetime.now(timezone.utc),
                last_command_duration_ms=1,
            )

        if not shutil.which(self._chdkptp_bin):
            self._camera_session_state = "unavailable"
            return CameraStatus(
                connection="error",
                chdkptp_available=False,
                camera_session_state="unavailable",
                last_successful_command_at=self._last_successful_command_at,
                last_command_duration_ms=self._last_command_duration_ms,
                last_error=f"{self._chdkptp_bin} not found in PATH",
            )

        started = datetime.now(timezone.utc)
        process = self._session.run_cli(args=["-elist"], timeout_seconds=5)
        self._last_command_duration_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
        if self._is_not_connected_error(process):
            self._camera_session_state = "unavailable"
            return CameraStatus(
                connection="disconnected",
                model="Canon IXUS 105",
                chdkptp_available=True,
                camera_session_state="unavailable",
                last_successful_command_at=self._last_successful_command_at,
                last_command_duration_ms=self._last_command_duration_ms,
                last_error=process.stderr.strip() or None,
            )
        if process.returncode != 0:
            self._camera_session_state = "error"
            return CameraStatus(
                connection="disconnected",
                chdkptp_available=True,
                camera_session_state="error",
                last_successful_command_at=self._last_successful_command_at,
                last_command_duration_ms=self._last_command_duration_ms,
                last_error=process.stderr.strip() or "camera unavailable",
            )
        probe = self._session.run(commands=["luar return 'PHOS_OK'"], timeout_seconds=5)
        self._last_command_duration_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
        if probe.returncode != 0 or self._is_not_connected_error(probe):
            self._camera_session_state = "unavailable"
            return CameraStatus(
                connection="disconnected",
                model="Canon IXUS 105",
                chdkptp_available=True,
                camera_session_state="unavailable",
                last_successful_command_at=self._last_successful_command_at,
                last_command_duration_ms=self._last_command_duration_ms,
                last_error=probe.stderr.strip() or "camera control unavailable",
            )
        self._camera_session_state = "idle"
        self._last_successful_command_at = datetime.now(timezone.utc)
        return CameraStatus(
            connection="connected",
            model="Canon IXUS 105",
            battery_percent=None,
            mode="record",
            chdkptp_available=True,
            camera_session_state="idle",
            last_successful_command_at=self._last_successful_command_at,
            last_command_duration_ms=self._last_command_duration_ms,
        )

    def switch_mode(self, mode: CameraMode) -> None:
        if mode not in ("record", "playback"):
            raise ValidationError("camera mode must be 'record' or 'playback'")
        if self._mock_mode:
            return
        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        chdk_mode = "rec" if mode == "record" else "play"
        process = self._session.run(commands=[chdk_mode], timeout_seconds=5)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or f"failed to switch camera mode to {mode}")

    def capture_photo(self) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = self._captures_dir / f"capture_{timestamp}.jpg"
        output_stem = output_file.with_suffix("")

        if self._mock_mode:
            output_file.write_bytes(b"PHOS_MOCK_CAPTURE")
            return output_file

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        if self._capture_reassert_manual:
            self._reassert_locked_manual_exposure_overrides()

        self._camera_session_state = "busy"
        started = datetime.now(timezone.utc)
        capture_command = f'remoteshoot "{output_stem}" -jpg'
        queued_attempts: list[list[str]] = [[capture_command]]
        tried_record_mode_retry = False
        tried_io_retry = False
        tried_reconnect_retry = False
        process = self._session.run(commands=queued_attempts[0], timeout_seconds=30)
        while process.returncode != 0:
            if not tried_record_mode_retry and self._needs_record_mode_retry(process):
                tried_record_mode_retry = True
                queued_attempts.append(["rec", capture_command])
            elif not tried_io_retry and self._is_transient_io_error(process):
                tried_io_retry = True
                queued_attempts.append([capture_command])
            elif not tried_reconnect_retry and self._is_not_connected_error(process):
                tried_reconnect_retry = True
                # Allow the USB/PTP stack a short settle window before reconnecting.
                time.sleep(0.3)
                queued_attempts.append(["c", "rec", capture_command])
            else:
                break

            next_attempt = queued_attempts.pop(1)
            process = self._session.run(commands=next_attempt, timeout_seconds=30)
        self._last_command_duration_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
        if process.returncode != 0:
            self._camera_session_state = "error"
            raise CameraUnavailableError(process.stderr.strip() or "capture failed")

        # remoteshoot may emit uppercase extension or variant suffixes.
        if not output_file.exists():
            matches = sorted(
                [path for path in self._captures_dir.glob(f"{output_stem.name}*") if path.is_file()],
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if not matches:
                self._camera_session_state = "error"
                details = "; ".join(
                    item
                    for item in [process.stderr.strip(), process.stdout.strip()]
                    if item
                )
                suffix = f" ({details})" if details else ""
                raise CameraUnavailableError(f"capture command succeeded but file was not downloaded{suffix}")
            if matches[0] != output_file:
                matches[0].replace(output_file)

        if not output_file.exists():
            self._camera_session_state = "error"
            details = "; ".join(
                item
                for item in [process.stderr.strip(), process.stdout.strip()]
                if item
            )
            suffix = f" ({details})" if details else ""
            raise CameraUnavailableError(f"capture command succeeded but file was not downloaded{suffix}")
        self._camera_session_state = "idle"
        self._last_successful_command_at = datetime.now(timezone.utc)
        return output_file

    def capture_live_view_frame(self) -> bytes:
        """Pull one JPEG from CHDK live view via remoteshoot -view=1.

        Canon often applies **display-oriented gain** to the live buffer, so brightness may not match the next still
        even in manual exposure. We never fall back to plain ``remoteshoot -jpg`` here: that would take real photos
        every frame and reset metering. After a successful frame, optional PHOS_LIVEVIEW_REASSERT_MANUAL can re-send
        Tv/ISO overrides if preview perturbs the body.
        """
        if self._mock_mode:
            latest = sorted(self._captures_dir.glob("capture_*.jpg"))
            if latest:
                return latest[-1].read_bytes()
            return b""

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        output_stem = self._captures_dir / f"liveview_{uuid4().hex}"
        live_view_command = f'remoteshoot "{output_stem}" -jpg -view=1'
        self._camera_session_state = "busy"
        started = datetime.now(timezone.utc)
        process = self._session.run(commands=[live_view_command], timeout_seconds=20)
        if process.returncode != 0 and self._is_unsupported_live_view_switch(process):
            self._camera_session_state = "error"
            raise CameraUnavailableError(
                "Live view needs remoteshoot with -view=1; this chdkptp build reports 'unknown switch view'. "
                "Upgrade chdkptp or disable live view. (A full JPEG remoteshoot fallback would fire real captures every frame.)"
            )
        if process.returncode != 0 and self._needs_record_mode_retry(process):
            process = self._session.run(commands=["rec", live_view_command], timeout_seconds=20)
        self._last_command_duration_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
        if process.returncode != 0:
            self._camera_session_state = "error"
            raise CameraUnavailableError(process.stderr.strip() or "live view frame capture failed")

        frame_candidates = sorted(
            [path for path in self._captures_dir.glob(f"{output_stem.name}*") if path.is_file()],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not frame_candidates:
            self._camera_session_state = "error"
            details = "; ".join(
                item
                for item in [process.stderr.strip(), process.stdout.strip()]
                if item
            )
            suffix = f" ({details})" if details else ""
            raise CameraUnavailableError(f"live view frame capture succeeded but no frame was downloaded{suffix}")

        frame_path = frame_candidates[0]
        frame_bytes = frame_path.read_bytes()
        for candidate in frame_candidates:
            candidate.unlink(missing_ok=True)

        if self._liveview_reassert_manual:
            self._reassert_locked_manual_exposure_overrides()

        self._camera_session_state = "idle"
        self._last_successful_command_at = datetime.now(timezone.utc)
        return frame_bytes

    def _reassert_locked_manual_exposure_overrides(self) -> None:
        """Re-send last fixed Tv/ISO/ND after paths that may alter Canon overrides (capture, live view, etc.)."""
        if self._mock_mode or self._exposure_ui_mode != "manual":
            return
        commands: list[str] = []
        if self._last_applied_manual_tv96 is not None:
            tv = int(self._last_applied_manual_tv96)
            commands.append(f"luar local tv={tv}; set_user_tv96(tv); set_tv96_direct(tv)")
        if self._last_applied_manual_iso is not None:
            iso = int(self._last_applied_manual_iso)
            if iso >= 50:
                commands.append(f"luar set_iso_mode({iso})")
            commands.append(f"luar set_iso_real({iso})")
        if self._last_applied_nd is not None:
            nd_arg = 1 if self._last_applied_nd else 2
            commands.append(
                "luar if type(set_nd_filter)=='function' and type(get_nd_present)=='function' "
                f"and select(1,get_nd_present())>0 then set_nd_filter({nd_arg}) sleep(100) end"
            )
        if not commands:
            return
        proc = self._session.run(commands=["rec", *commands], timeout_seconds=12)
        if proc.returncode != 0:
            return

    @staticmethod
    def _command_output(process) -> str:
        return "\n".join(item for item in [process.stdout, process.stderr] if item).lower()

    @classmethod
    def _needs_record_mode_retry(cls, process) -> bool:
        output = cls._command_output(process)
        return "not in rec" in output or "record mode" in output

    @classmethod
    def _is_transient_io_error(cls, process) -> bool:
        output = cls._command_output(process)
        return "i/o error" in output or "timed out" in output

    @classmethod
    def _is_not_connected_error(cls, process) -> bool:
        output = cls._command_output(process)
        return (
            "not connected" in output
            or "no matching devices found" in output
            or "no cameras" in output
        )

    @classmethod
    def _is_unsupported_live_view_switch(cls, process) -> bool:
        output = cls._command_output(process)
        return "unknown switch view" in output

    def run_script(self, profile: ScriptProfile) -> ScriptExecutionResult:
        run_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        if self._mock_mode:
            self._camera_session_state = "busy"
            result = ScriptExecutionResult(
                run_id=run_id,
                profile_name=profile.name,
                state="completed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                stdout=f"mock script executed: {profile.name}",
                stderr="",
                exit_code=0,
                artifacts=list(profile.expected_artifacts),
            )
            self._camera_session_state = "idle"
            self._script_runs[run_id] = result
            return result

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")
        if not profile.commands:
            raise ValidationError("script profile commands cannot be empty")

        self._camera_session_state = "busy"
        started = datetime.now(timezone.utc)
        process = self._session.run(commands=profile.commands, timeout_seconds=profile.timeout_seconds)
        self._last_command_duration_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))
        result = ScriptExecutionResult(
            run_id=run_id,
            profile_name=profile.name,
            state=parse_script_state(process.returncode),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            stdout=process.stdout,
            stderr=process.stderr,
            exit_code=process.returncode,
            artifacts=collect_artifacts(profile.expected_artifacts, process.stdout),
        )
        if result.state == "completed":
            self._last_successful_command_at = datetime.now(timezone.utc)
            self._camera_session_state = "idle"
        elif result.state == "running":
            self._camera_session_state = "busy"
        else:
            self._camera_session_state = "error"
        self._script_runs[run_id] = result
        if result.state == "failed":
            raise CameraUnavailableError(result.stderr.strip() or f"script {profile.name} failed")
        return result

    def get_manual_state(self) -> CameraManualState:
        now = datetime.now(timezone.utc)
        if self._mock_mode:
            zs = 11
            fake_fl = [5 + i for i in range(zs)]
            positions = tuple(
                CameraZoomPosition(
                    step=i,
                    focal_length_mm=fl,
                    focal_length_35mm_equiv_mm=max(1, int(round(fl * self._focal_35mm_equiv_mult))),
                )
                for i, fl in enumerate(fake_fl)
            )
            zstep = self._manual_state_cache.zoom_step if self._manual_state_cache.zoom_step is not None else 0
            zfl = fake_fl[zstep] if 0 <= zstep < len(fake_fl) else None
            return CameraManualState(
                power_state=self._manual_state_cache.power_state,
                mode="record",
                shutter_seconds=self._manual_state_cache.shutter_seconds,
                shutter_display=self._manual_state_cache.shutter_display,
                iso=self._manual_state_cache.iso or 100,
                aperture_display=self._manual_state_cache.aperture_display,
                nd_enabled=self._manual_state_cache.nd_enabled,
                zoom_step=self._manual_state_cache.zoom_step,
                focus_mm=self._manual_state_cache.focus_mm,
                flash_mode=self._manual_state_cache.flash_mode,
                last_interaction_at=self._manual_state_cache.last_interaction_at,
                idle_seconds=max(0, int((now - self._manual_state_cache.last_interaction_at).total_seconds())),
                capabilities=self._manual_state_cache.capabilities,
                exposure_control=self._manual_state_cache.exposure_control,
                metering_shutter_display=self._manual_state_cache.metering_shutter_display,
                metering_iso=self._manual_state_cache.metering_iso,
                shutter_auto_active=self._shutter_auto_active,
                iso_auto_active=self._iso_auto_active,
                focus_auto_active=self._focus_auto_active,
                zoom_focal_length_mm=zfl,
                zoom_steps_count=zs,
                zoom_positions=positions,
                focus_control=self._manual_state_cache.focus_control,
            )

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        process = self._session.run(
            commands=[
                'luar local function phosn(f,d) if type(f)~="function" then return d end local ok,a=pcall(f) '
                'if not ok or a==nil then return d end if type(a)=="number" then return a end '
                'local s=select(1,a) if type(s)~="number" then return tonumber(tostring(a)) or d end return s end '
                "local tv96=get_tv96(); local iso_real=get_iso_real(); "
                "local zoom=select(1,get_zoom()); local focus=select(1,get_focus()); local flash_mode=select(1,get_flash_mode()); "
                "local mode_raw=select(1,get_mode()); local nd_present=select(1,get_nd_present()); "
                "local nd_current_ev96=select(1,get_nd_current_ev96()); "
                "local nd_value_ev96=phosn(get_nd_value_ev96,-1); "
                'local fl=phosn(get_focal_length,-1); local zsteps=phosn(get_zoom_steps,-1); local fm=phosn(get_focus_mode,-1); '
                "return string.format('PHOS:%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s',"
                "tostring(tv96),tostring(iso_real),tostring(zoom),tostring(focus),tostring(flash_mode),tostring(mode_raw),"
                "tostring(nd_present),tostring(nd_current_ev96),tostring(fl),tostring(zsteps),tostring(fm),tostring(nd_value_ev96))"
            ],
            timeout_seconds=10,
        )
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "manual state query failed")

        parsed = self._parse_manual_state_output(process.stdout)
        if parsed is None:
            return CameraManualState(
                power_state=self._manual_state_cache.power_state,
                mode=self._manual_state_cache.mode,
                shutter_seconds=self._manual_state_cache.shutter_seconds,
                shutter_display=self._manual_state_cache.shutter_display,
                iso=self._manual_state_cache.iso,
                aperture_display=self._manual_state_cache.aperture_display,
                nd_enabled=self._manual_state_cache.nd_enabled,
                zoom_step=self._manual_state_cache.zoom_step,
                focus_mm=self._manual_state_cache.focus_mm,
                flash_mode=self._manual_state_cache.flash_mode,
                last_interaction_at=self._manual_state_cache.last_interaction_at,
                idle_seconds=max(0, int((now - self._manual_state_cache.last_interaction_at).total_seconds())),
                capabilities=self._manual_state_cache.capabilities,
                exposure_control=self._manual_state_cache.exposure_control,
                metering_shutter_display=self._manual_state_cache.metering_shutter_display,
                metering_iso=self._manual_state_cache.metering_iso,
                shutter_auto_active=self._shutter_auto_active,
                iso_auto_active=self._iso_auto_active,
                focus_auto_active=self._manual_state_cache.focus_auto_active,
                zoom_focal_length_mm=self._manual_state_cache.zoom_focal_length_mm,
                zoom_steps_count=self._manual_state_cache.zoom_steps_count,
                zoom_positions=self._manual_state_cache.zoom_positions,
                focus_control=self._manual_state_cache.focus_control,
            )

        (
            tv96,
            iso_real,
            zoom,
            focus,
            flash_mode,
            mode_raw,
            nd_present,
            nd_current_ev96,
            focal_raw,
            zsteps,
            focus_mode_raw,
            nd_value_ev96,
        ) = parsed
        self._ensure_zoom_focal_table(zsteps)
        zoom_positions = self._zoom_positions_tuple()
        zoom_focal_length_mm = focal_raw if focal_raw >= 0 else None
        zoom_steps_count = zsteps if zsteps > 0 else None
        focus_control = self._map_focus_mode(focus_mode_raw)
        meter_sec = self._tv96_to_seconds(tv96) if tv96 != -9999 else None
        meter_display = self._format_shutter(meter_sec)
        meter_iso = iso_real if iso_real > 0 else None

        if self._exposure_ui_mode == "auto":
            exposure_control = "auto"
            shutter_seconds = meter_sec
            iso_out = meter_iso
        elif self._exposure_ui_mode == "manual":
            exposure_control = "manual"
            shutter_seconds = meter_sec
            iso_out = meter_iso if meter_iso is not None else self._manual_state_cache.iso
            if self._shutter_auto_active:
                shutter_seconds = None
            elif self._last_applied_manual_tv96 is not None:
                shutter_seconds = self._tv96_to_seconds(self._last_applied_manual_tv96)
            if self._iso_auto_active:
                iso_out = None
            elif self._last_applied_manual_iso is not None:
                iso_out = self._last_applied_manual_iso
        else:
            exposure_control = "unknown"
            shutter_seconds = meter_sec
            iso_out = meter_iso if meter_iso is not None else self._manual_state_cache.iso
            if self._shutter_auto_active:
                shutter_seconds = None
            elif self._last_applied_manual_tv96 is not None:
                shutter_seconds = self._tv96_to_seconds(self._last_applied_manual_tv96)
            if self._iso_auto_active:
                iso_out = None
            elif self._last_applied_manual_iso is not None:
                iso_out = self._last_applied_manual_iso

        mode: CameraMode = "record" if mode_raw == 1 else "playback"
        nd_enabled = None
        if nd_present > 0:
            if nd_current_ev96 == 0:
                nd_hw_in = False
            elif nd_value_ev96 > 0:
                nd_hw_in = nd_current_ev96 >= nd_value_ev96 - 2
            else:
                nd_hw_in = nd_current_ev96 > 0
            if self._exposure_ui_mode == "manual" and self._last_applied_nd is not None:
                nd_enabled = self._last_applied_nd
            else:
                nd_enabled = nd_hw_in
        focus_mm_out = focus if focus >= 0 else self._manual_state_cache.focus_mm
        if self._focus_auto_active and self._exposure_ui_mode != "auto":
            focus_mm_out = None
        state = CameraManualState(
            power_state=self._manual_state_cache.power_state,
            mode=mode,
            shutter_seconds=shutter_seconds,
            shutter_display=self._format_shutter(shutter_seconds),
            iso=iso_out,
            aperture_display="ND on" if nd_enabled else "ND off" if nd_enabled is not None else "auto",
            nd_enabled=nd_enabled,
            zoom_step=zoom if zoom >= 0 else self._manual_state_cache.zoom_step,
            focus_mm=focus_mm_out,
            flash_mode=flash_mode if flash_mode >= 0 else self._manual_state_cache.flash_mode,
            last_interaction_at=self._manual_state_cache.last_interaction_at,
            idle_seconds=max(0, int((now - self._manual_state_cache.last_interaction_at).total_seconds())),
            capabilities=CameraManualCapabilities(
                supports_nd_filter=nd_present > 0,
            ),
            exposure_control=exposure_control,
            metering_shutter_display=meter_display,
            metering_iso=meter_iso,
            shutter_auto_active=self._shutter_auto_active,
            iso_auto_active=self._iso_auto_active,
            focus_auto_active=self._focus_auto_active,
            zoom_focal_length_mm=zoom_focal_length_mm,
            zoom_steps_count=zoom_steps_count,
            zoom_positions=zoom_positions,
            focus_control=focus_control,
        )
        self._manual_state_cache = state
        return state

    def apply_manual_settings(self, settings: CameraManualSettings) -> CameraManualState:
        commands: list[str] = ["rec"]
        if settings.exposure_auto:
            # Omitting shutter/ISO does not clear prior CHDK overrides; actively restore AE + auto ISO.
            commands.append(
                'luar local c=require("capmode"); '
                'if c.valid("P") then c.set("P") '
                'elseif c.valid("AUTO") then c.set("AUTO") end'
            )
            commands.append("luar set_iso_mode(0)")
            commands.append("luar set_aelock(0)")
            commands.append("luar set_aflock(0)")
            commands.append("luar set_mf(0)")
        else:
            # Program / Auto ignores fixed Tv; switch to a manual-capable mode first.
            commands.append(
                'luar local c=require("capmode"); '
                'if c.valid("M") then c.set("M") '
                'elseif c.valid("TV") then c.set("TV") end'
            )
            commands.append("luar set_aelock(0)")
            if settings.shutter_auto:
                pass
            elif settings.shutter_seconds is not None:
                if settings.shutter_seconds <= 0:
                    raise ValidationError("shutter_seconds must be > 0")
                tv96 = self._seconds_to_tv96(settings.shutter_seconds)
                # set_tv96_direct alone can leave Canon acting like AE; set_user_tv96 fixes the M/Tv dial slot first.
                commands.append(f"luar local tv={tv96}; set_user_tv96(tv); set_tv96_direct(tv)")
            if settings.iso_auto:
                commands.append("luar set_iso_mode(0)")
            elif settings.iso is not None:
                if settings.iso < 40 or settings.iso > 6400:
                    raise ValidationError("iso must be between 40 and 6400")
                # set_iso_real alone leaves PROPCASE_ISO_MODE on Auto; get_iso_real() then stays ~metered (e.g. 46).
                if settings.iso >= 50:
                    commands.append(f"luar set_iso_mode({int(settings.iso)})")
                commands.append(f"luar set_iso_real({int(settings.iso)})")
        if settings.zoom_step is not None:
            if settings.zoom_step < 0:
                raise ValidationError("zoom_step must be >= 0")
            commands.append(f"luar set_zoom({int(settings.zoom_step)})")
            manual_focus_next = not settings.focus_auto and settings.focus_mm is not None
            if manual_focus_next and self._focus_after_zoom_ms > 0:
                commands.append(f"luar sleep({int(self._focus_after_zoom_ms)})")
        if settings.focus_auto:
            commands.append("luar set_aflock(0); set_mf(0)")
        elif settings.focus_mm is not None:
            if settings.focus_mm < 0:
                raise ValidationError("focus_mm must be >= 0")
            settle = int(self._focus_settle_ms)
            if self._focus_use_aflock:
                commands.append(
                    f"luar set_mf(1); set_aflock(1); sleep(350); set_focus({int(settings.focus_mm)}); sleep({settle})"
                )
            else:
                commands.append(f"luar set_mf(1); set_focus({int(settings.focus_mm)}); sleep({settle})")
        if settings.flash_mode is not None:
            commands.append(f"luar set_prop(143,{int(settings.flash_mode)})")
        # ND last: CHDK applies ND after exposure; Tv/ISO/zoom/focus can reset it if set earlier.
        if settings.nd_enabled is not None:
            nd_arg = 1 if settings.nd_enabled else 2
            commands.append(
                "luar if type(set_nd_filter)=='function' and type(get_nd_present)=='function' "
                f"and select(1,get_nd_present())>0 then set_nd_filter({nd_arg}) sleep(150) end"
            )

        if len(commands) == 1:
            return self.touch()
        # Long exposures / mode switches can exceed 20s on USB + IXUS class cams.
        process = self._session.run(commands=commands, timeout_seconds=45)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "manual settings apply failed")
        self._manual_state_cache = self._manual_state_cache
        if settings.exposure_auto:
            self._last_applied_manual_tv96 = None
            self._last_applied_manual_iso = None
            self._last_applied_nd = None
            self._exposure_ui_mode = "auto"
            self._shutter_auto_active = False
            self._iso_auto_active = False
            self._focus_auto_active = False
        else:
            self._exposure_ui_mode = "manual"
            self._shutter_auto_active = settings.shutter_auto
            self._iso_auto_active = settings.iso_auto
            self._focus_auto_active = settings.focus_auto
            if settings.shutter_auto:
                self._last_applied_manual_tv96 = None
            elif settings.shutter_seconds is not None:
                self._last_applied_manual_tv96 = self._seconds_to_tv96(settings.shutter_seconds)
            if settings.iso_auto:
                self._last_applied_manual_iso = None
            elif settings.iso is not None:
                self._last_applied_manual_iso = int(settings.iso)
            if settings.nd_enabled is not None:
                self._last_applied_nd = settings.nd_enabled
        return self.touch()

    def sleep(self, level: str) -> CameraManualState:
        if level == "sleep":
            commands = ["play"]
            power_state = "sleep"
        elif level == "deep_sleep":
            commands = ["play", "luar set_lcd_display(0)", "luar set_backlight(0)"]
            power_state = "deep_sleep"
        else:
            raise ValidationError("sleep level must be 'sleep' or 'deep_sleep'")
        process = self._session.run(commands=commands, timeout_seconds=10)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "camera sleep failed")
        self._manual_state_cache = CameraManualState(
            power_state=power_state,  # type: ignore[arg-type]
            mode="playback",
            shutter_seconds=self._manual_state_cache.shutter_seconds,
            shutter_display=self._manual_state_cache.shutter_display,
            iso=self._manual_state_cache.iso,
            aperture_display=self._manual_state_cache.aperture_display,
            nd_enabled=self._manual_state_cache.nd_enabled,
            zoom_step=self._manual_state_cache.zoom_step,
            focus_mm=self._manual_state_cache.focus_mm,
            flash_mode=self._manual_state_cache.flash_mode,
            last_interaction_at=self._manual_state_cache.last_interaction_at,
            idle_seconds=0,
            capabilities=self._manual_state_cache.capabilities,
            exposure_control=self._manual_state_cache.exposure_control,
            metering_shutter_display=self._manual_state_cache.metering_shutter_display,
            metering_iso=self._manual_state_cache.metering_iso,
            shutter_auto_active=self._manual_state_cache.shutter_auto_active,
            iso_auto_active=self._manual_state_cache.iso_auto_active,
            focus_auto_active=self._manual_state_cache.focus_auto_active,
            zoom_focal_length_mm=self._manual_state_cache.zoom_focal_length_mm,
            zoom_steps_count=self._manual_state_cache.zoom_steps_count,
            zoom_positions=self._manual_state_cache.zoom_positions,
            focus_control=self._manual_state_cache.focus_control,
        )
        return self.get_manual_state()

    def wake(self) -> CameraManualState:
        self._manual_state_cache = CameraManualState(
            power_state="waking",
            mode=self._manual_state_cache.mode,
            shutter_seconds=self._manual_state_cache.shutter_seconds,
            shutter_display=self._manual_state_cache.shutter_display,
            iso=self._manual_state_cache.iso,
            aperture_display=self._manual_state_cache.aperture_display,
            nd_enabled=self._manual_state_cache.nd_enabled,
            zoom_step=self._manual_state_cache.zoom_step,
            focus_mm=self._manual_state_cache.focus_mm,
            flash_mode=self._manual_state_cache.flash_mode,
            last_interaction_at=self._manual_state_cache.last_interaction_at,
            idle_seconds=self._manual_state_cache.idle_seconds,
            capabilities=self._manual_state_cache.capabilities,
            exposure_control=self._manual_state_cache.exposure_control,
            metering_shutter_display=self._manual_state_cache.metering_shutter_display,
            metering_iso=self._manual_state_cache.metering_iso,
            shutter_auto_active=self._manual_state_cache.shutter_auto_active,
            iso_auto_active=self._manual_state_cache.iso_auto_active,
            focus_auto_active=self._manual_state_cache.focus_auto_active,
            zoom_focal_length_mm=self._manual_state_cache.zoom_focal_length_mm,
            zoom_steps_count=self._manual_state_cache.zoom_steps_count,
            zoom_positions=self._manual_state_cache.zoom_positions,
            focus_control=self._manual_state_cache.focus_control,
        )
        process = self._session.run(commands=["luar set_lcd_display(1)", "luar set_backlight(1)", "rec"], timeout_seconds=10)
        if process.returncode != 0:
            self._manual_state_cache = CameraManualState(
                power_state="error",
                mode=self._manual_state_cache.mode,
                shutter_seconds=self._manual_state_cache.shutter_seconds,
                shutter_display=self._manual_state_cache.shutter_display,
                iso=self._manual_state_cache.iso,
                aperture_display=self._manual_state_cache.aperture_display,
                nd_enabled=self._manual_state_cache.nd_enabled,
                zoom_step=self._manual_state_cache.zoom_step,
                focus_mm=self._manual_state_cache.focus_mm,
                flash_mode=self._manual_state_cache.flash_mode,
                last_interaction_at=self._manual_state_cache.last_interaction_at,
                idle_seconds=self._manual_state_cache.idle_seconds,
                capabilities=self._manual_state_cache.capabilities,
                exposure_control=self._manual_state_cache.exposure_control,
                metering_shutter_display=self._manual_state_cache.metering_shutter_display,
                metering_iso=self._manual_state_cache.metering_iso,
                shutter_auto_active=self._manual_state_cache.shutter_auto_active,
                iso_auto_active=self._manual_state_cache.iso_auto_active,
                focus_auto_active=self._manual_state_cache.focus_auto_active,
                zoom_focal_length_mm=self._manual_state_cache.zoom_focal_length_mm,
                zoom_steps_count=self._manual_state_cache.zoom_steps_count,
                zoom_positions=self._manual_state_cache.zoom_positions,
                focus_control=self._manual_state_cache.focus_control,
            )
            raise CameraUnavailableError(process.stderr.strip() or "camera wake failed")
        return self.touch()

    def touch(self) -> CameraManualState:
        self._manual_state_cache = CameraManualState(
            power_state="active",
            mode=self._manual_state_cache.mode,
            shutter_seconds=self._manual_state_cache.shutter_seconds,
            shutter_display=self._manual_state_cache.shutter_display,
            iso=self._manual_state_cache.iso,
            aperture_display=self._manual_state_cache.aperture_display,
            nd_enabled=self._manual_state_cache.nd_enabled,
            zoom_step=self._manual_state_cache.zoom_step,
            focus_mm=self._manual_state_cache.focus_mm,
            flash_mode=self._manual_state_cache.flash_mode,
            last_interaction_at=datetime.now(timezone.utc),
            idle_seconds=0,
            capabilities=self._manual_state_cache.capabilities,
            exposure_control=self._manual_state_cache.exposure_control,
            metering_shutter_display=self._manual_state_cache.metering_shutter_display,
            metering_iso=self._manual_state_cache.metering_iso,
            shutter_auto_active=self._manual_state_cache.shutter_auto_active,
            iso_auto_active=self._manual_state_cache.iso_auto_active,
            focus_auto_active=self._manual_state_cache.focus_auto_active,
            zoom_focal_length_mm=self._manual_state_cache.zoom_focal_length_mm,
            zoom_steps_count=self._manual_state_cache.zoom_steps_count,
            zoom_positions=self._manual_state_cache.zoom_positions,
            focus_control=self._manual_state_cache.focus_control,
        )
        return self.get_manual_state()

    def stop_script(self, run_id: str) -> None:
        result = self._script_runs.get(run_id)
        if not result:
            raise NotFoundError(f"script run {run_id} not found")
        self._script_runs[run_id] = ScriptExecutionResult(
            run_id=result.run_id,
            profile_name=result.profile_name,
            state="stopped",
            started_at=result.started_at,
            finished_at=datetime.now(timezone.utc),
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            artifacts=result.artifacts,
        )

    def get_script_status(self, run_id: str) -> ScriptExecutionResult | None:
        return self._script_runs.get(run_id)

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        if self._mock_mode:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(b"PHOS_MOCK_DOWNLOAD")
            return local_path
        process = self._session.run(commands=[f'download -s "{remote_path}" "{local_path}"'], timeout_seconds=60)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "download failed")
        return local_path

    def list_files(self, remote_dir: str) -> list[str]:
        if self._mock_mode:
            return []
        process = self._session.run(commands=[f'ls "{remote_dir}"'], timeout_seconds=10)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "list files failed")
        return [line.strip() for line in process.stdout.splitlines() if line.strip()]

    def _map_focus_mode(self, raw: int) -> Literal["af", "mf", "unknown"]:
        if raw < 0:
            return "unknown"
        if raw == 0:
            return "af"
        return "mf"

    def _zoom_positions_tuple(self) -> tuple[CameraZoomPosition, ...]:
        if not self._zoom_focal_by_step:
            return ()
        return tuple(
            CameraZoomPosition(
                step=i,
                focal_length_mm=fl,
                focal_length_35mm_equiv_mm=max(1, int(round(fl * self._focal_35mm_equiv_mult))),
            )
            for i, fl in enumerate(self._zoom_focal_by_step)
        )

    def _ensure_zoom_focal_table(self, zoom_steps: int) -> None:
        if self._zoom_focal_by_step is not None:
            return
        if zoom_steps <= 0:
            self._zoom_focal_by_step = []
            return
        if self._mock_mode:
            self._zoom_focal_by_step = [5 + i for i in range(zoom_steps)]
            return
        lua = (
            'luar if type(get_focal_length)~="function" then return "FLTABLE:" end '
            "local n=type(get_zoom_steps)=='function' and select(1,get_zoom_steps()) or -1 "
            "if not n or n<1 then return 'FLTABLE:' end; "
            "local cur=select(1,get_zoom()) or 0; local out={}; "
            'for i=0,n-1 do set_zoom(i) sleep(55) local fl=0; if type(get_focal_length)=="function" then '
            "local ok,v=pcall(get_focal_length); if ok and v~=nil then fl=type(v)=='number' and v or select(1,v) or 0 end end; "
            "out[#out+1]=tostring(fl or 0) end; "
            "set_zoom(cur) sleep(50) return 'FLTABLE:'..table.concat(out,';')"
        )
        proc = self._session.run(commands=["rec", lua], timeout_seconds=45)
        if proc.returncode != 0:
            self._zoom_focal_by_step = []
            return
        match = re.search(r"FLTABLE:([^\s\n]+)", proc.stdout)
        if not match:
            self._zoom_focal_by_step = []
            return
        body = (match.group(1) or "").strip()
        if not body:
            self._zoom_focal_by_step = []
            return
        try:
            self._zoom_focal_by_step = [max(0, int(round(float(x)))) for x in body.split(";") if x.strip() != ""]
        except ValueError:
            self._zoom_focal_by_step = []

    @staticmethod
    def _seconds_to_tv96(seconds: float) -> int:
        return int(round(-96.0 * math.log2(seconds)))

    @staticmethod
    def _tv96_to_seconds(tv96: int) -> float:
        return 2 ** (-tv96 / 96.0)

    @staticmethod
    def _format_shutter(seconds: float | None) -> str:
        if seconds is None:
            return "auto"
        if seconds >= 1:
            return f'{seconds:.1f}"'
        denominator = max(1, int(round(1.0 / seconds)))
        return f"1/{denominator}"

    @staticmethod
    def _parse_manual_state_output(stdout: str) -> tuple[int, ...] | None:
        match = re.search(r"PHOS:([^\s\n]+)", stdout)
        if not match:
            return None
        parts = match.group(1).split(",")
        if len(parts) < 8:
            return None
        while len(parts) < 12:
            parts.append("-1")

        def _parse_int(raw: str, default: int) -> int:
            value = raw.strip().lower()
            if value in {"nil", "none"}:
                return default
            try:
                return int(round(float(value)))
            except ValueError:
                return default

        def _parse_boolish_int(raw: str, default: int = 0) -> int:
            value = raw.strip().lower()
            if value == "true":
                return 1
            if value == "false":
                return 0
            return _parse_int(value, default)

        return (
            _parse_int(parts[0], -9999),
            _parse_int(parts[1], -1),
            _parse_int(parts[2], -1),
            _parse_int(parts[3], -1),
            _parse_int(parts[4], -1),
            _parse_int(parts[5], -1),
            _parse_boolish_int(parts[6], 0),
            _parse_int(parts[7], 0),
            _parse_int(parts[8], -1),
            _parse_int(parts[9], -1),
            _parse_int(parts[10], -1),
            _parse_int(parts[11], -1),
        )
