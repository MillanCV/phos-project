from __future__ import annotations

from pathlib import Path

import pytest

from src.camera.chdkptp.gateway import ChdkptpCameraGateway  # type: ignore[import-not-found]
from src.camera.chdkptp.session import ChdkptpSessionResult  # type: ignore[import-not-found]
from src.shared.errors import CameraUnavailableError  # type: ignore[import-not-found]


class FakeSession:
    def __init__(self, captures_dir: Path, responses: list[tuple[int, str, str]]) -> None:
        self._captures_dir = captures_dir
        self._responses = responses
        self.calls: list[list[str]] = []

    def run(self, commands: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        self.calls.append(commands)
        returncode, stdout, stderr = self._responses.pop(0)
        if returncode == 0:
            stem = _extract_capture_stem(commands)
            if stem:
                path = Path(stem + ".JPG")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"JPEGDATA")
        return ChdkptpSessionResult(
            command=["chdkptp", *commands],
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
        )


def _extract_capture_stem(commands: list[str]) -> str | None:
    for item in commands:
        if not item.startswith('remoteshoot "'):
            continue
        _, _, rest = item.partition('remoteshoot "')
        stem, _, _ = rest.partition('" -jpg')
        return stem or None
    return None


def test_capture_photo_retries_with_record_mode_when_needed(tmp_path, monkeypatch):
    monkeypatch.setattr("src.camera.chdkptp.gateway.shutil.which", lambda _: "/usr/bin/chdkptp")
    gateway = ChdkptpCameraGateway(captures_dir=tmp_path / "captures")
    fake = FakeSession(
        captures_dir=tmp_path / "captures",
        responses=[
            (1, "", "ERROR: not in rec"),
            (0, "captured", ""),
        ],
    )
    gateway._session = fake  # type: ignore[attr-defined]

    photo = gateway.capture_photo()

    assert photo.exists()
    assert photo.suffix == ".jpg"
    assert len(fake.calls) == 2
    assert fake.calls[0][0].startswith("remoteshoot")
    assert fake.calls[1][0] == "rec"


def test_capture_photo_retries_once_on_io_error(tmp_path, monkeypatch):
    monkeypatch.setattr("src.camera.chdkptp.gateway.shutil.which", lambda _: "/usr/bin/chdkptp")
    gateway = ChdkptpCameraGateway(captures_dir=tmp_path / "captures")
    fake = FakeSession(
        captures_dir=tmp_path / "captures",
        responses=[
            (1, "", "ERROR: I/O error"),
            (0, "captured", ""),
        ],
    )
    gateway._session = fake  # type: ignore[attr-defined]

    photo = gateway.capture_photo()

    assert photo.exists()
    assert len(fake.calls) == 2
    assert fake.calls[0][0].startswith("remoteshoot")
    assert fake.calls[1][0].startswith("remoteshoot")


def test_capture_photo_raises_when_retries_exhausted(tmp_path, monkeypatch):
    monkeypatch.setattr("src.camera.chdkptp.gateway.shutil.which", lambda _: "/usr/bin/chdkptp")
    gateway = ChdkptpCameraGateway(captures_dir=tmp_path / "captures")
    fake = FakeSession(
        captures_dir=tmp_path / "captures",
        responses=[
            (1, "", "ERROR: not in rec"),
            (1, "", "ERROR: I/O error"),
            (1, "", "ERROR: I/O error"),
        ],
    )
    gateway._session = fake  # type: ignore[attr-defined]

    with pytest.raises(CameraUnavailableError):
        gateway.capture_photo()

