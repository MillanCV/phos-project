from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from uuid import uuid4

from src.camera.chdkptp.output_parser import collect_artifacts, parse_script_state
from src.camera.chdkptp.session import ChdkptpSession
from src.camera.domain import CameraMode, CameraStatus, ScriptExecutionResult, ScriptProfile
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
        if "no cameras" in process.stdout.lower():
            self._camera_session_state = "idle"
            return CameraStatus(
                connection="disconnected",
                model="Canon IXUS 105",
                chdkptp_available=True,
                camera_session_state="idle",
                last_successful_command_at=self._last_successful_command_at,
                last_command_duration_ms=self._last_command_duration_ms,
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

        self._camera_session_state = "busy"
        started = datetime.now(timezone.utc)
        commands = [
            "rec",
            f'remoteshoot "{output_stem}" -jpg',
        ]
        process = self._session.run(commands=commands, timeout_seconds=30)
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
