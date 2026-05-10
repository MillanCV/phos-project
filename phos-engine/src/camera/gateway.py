from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess

from src.camera.domain import CameraStatus
from src.shared.errors import CameraUnavailableError


class ChdkptpCameraGateway:
    def __init__(self, captures_dir: Path) -> None:
        self._captures_dir = captures_dir
        self._captures_dir.mkdir(parents=True, exist_ok=True)
        self._chdkptp_bin = os.getenv("CHDKPTP_BIN", "chdkptp")
        self._mock_mode = os.getenv("PHOS_CAMERA_MOCK", "false").lower() == "true"

    def get_status(self) -> CameraStatus:
        if self._mock_mode:
            return CameraStatus(connection="connected", model="Canon IXUS 105 (mock)", battery_percent=100)

        if not shutil.which(self._chdkptp_bin):
            return CameraStatus(connection="error", last_error=f"{self._chdkptp_bin} not found in PATH")

        # Keep the status check lightweight: query camera list.
        process = subprocess.run(
            [self._chdkptp_bin, "-elist"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if process.returncode != 0:
            return CameraStatus(connection="disconnected", last_error=process.stderr.strip() or "camera unavailable")
        if "no cameras" in process.stdout.lower():
            return CameraStatus(connection="disconnected", model="Canon IXUS 105")

        return CameraStatus(connection="connected", model="Canon IXUS 105", battery_percent=None)

    def capture_photo(self) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = self._captures_dir / f"capture_{timestamp}.jpg"

        if self._mock_mode:
            output_file.write_bytes(b"PHOS_MOCK_CAPTURE")
            return output_file

        if not shutil.which(self._chdkptp_bin):
            raise CameraUnavailableError(f"{self._chdkptp_bin} not found in PATH")

        # Minimal, robust command for remote shoot to camera card and then download.
        # These commands may vary by CHDK script version; errors are surfaced to caller.
        script = [
            "rec",
            "shoot",
            f'download -s A/DCIM/100CANON/IMG_0001.JPG "{output_file}"',
        ]
        command = [self._chdkptp_bin]
        for item in script:
            command.extend(["-e", item])

        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
        if process.returncode != 0:
            raise CameraUnavailableError(process.stderr.strip() or "capture failed")
        if not output_file.exists():
            raise CameraUnavailableError("capture command succeeded but file was not downloaded")
        return output_file
