from __future__ import annotations

import subprocess

from src.camera.chdkptp.session import ChdkptpSession  # type: ignore[import-not-found]


def test_run_command_timeout_returns_non_throwing_result(monkeypatch):
    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.TimeoutExpired(cmd=["chdkptp"], timeout=5, output="", stderr="")

    monkeypatch.setattr("src.camera.chdkptp.session.subprocess.run", fake_run)

    session = ChdkptpSession("chdkptp")
    result = session._run_command(["chdkptp", "-elist"], timeout_seconds=5)

    assert result.returncode == 124
    assert "timed out" in result.stderr
