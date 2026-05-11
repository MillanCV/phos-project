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

    def get_status(self) -> CameraStatus:
        if self._mock_mode:
            return CameraStatus(connection="connected", model="Canon IXUS 105 (mock)", battery_percent=100, mode="record")

        if not shutil.which(self._chdkptp_bin):
            return CameraStatus(connection="error", last_error=f"{self._chdkptp_bin} not found in PATH")

        process = self._session.run_cli(args=["-elist"], timeout_seconds=5)
        if process.returncode != 0:
            return CameraStatus(connection="disconnected", last_error=process.stderr.strip() or "camera unavailable")
        if "no cameras" in process.stdout.lower():
            return CameraStatus(connection="disconnected", model="Canon IXUS 105")
        return CameraStatus(connection="connected", model="Canon IXUS 105", battery_percent=None, mode="record")

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

        if self._mock_mode:
            output_file.write_bytes(b"PHOS_MOCK_CAPTURE")
            return output_file

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        commands = [
            "rec",
            "shoot",
            f'download -s A/DCIM/100CANON/IMG_0001.JPG "{output_file}"',
        ]
        process = self._session.run(commands=commands, timeout_seconds=30)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "capture failed")
        if not output_file.exists():
            raise CameraUnavailableError("capture command succeeded but file was not downloaded")
        return output_file

    def run_script(self, profile: ScriptProfile) -> ScriptExecutionResult:
        run_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        if self._mock_mode:
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
            self._script_runs[run_id] = result
            return result

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")
        if not profile.commands:
            raise ValidationError("script profile commands cannot be empty")

        process = self._session.run(commands=profile.commands, timeout_seconds=profile.timeout_seconds)
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
