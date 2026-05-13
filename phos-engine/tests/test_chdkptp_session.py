from __future__ import annotations

import subprocess

from src.camera.chdkptp.session import (  # type: ignore[import-not-found]
    ChdkptpSession,
    _pretty_chdkptp_argv_log,
    _summarize_chdkptp_command,
)


def test_run_command_timeout_returns_non_throwing_result(monkeypatch):
    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.TimeoutExpired(cmd=["chdkptp"], timeout=5, output="", stderr="")

    monkeypatch.setattr("src.camera.chdkptp.session.subprocess.run", fake_run)

    session = ChdkptpSession("chdkptp")
    result = session._run_command(["chdkptp", "-elist"], timeout_seconds=5)

    assert result.returncode == 124
    assert "timed out" in result.stderr


def test_summarize_elist() -> None:
    assert _summarize_chdkptp_command(["/bin/chdkptp.sh", "-elist"]) == "elist"


def test_summarize_probe_phos_ok() -> None:
    assert _summarize_chdkptp_command(["/b", "-ec", "-eluar return 'PHOS_OK'"]) == "probe PHOS_OK"


def test_summarize_manual_state_lua() -> None:
    lua = "local x=1; get_tv96(); return 'PHOS:1,2'"
    assert _summarize_chdkptp_command(["/b", "-ec", f"-eluar {lua}"]) == "lua manual_state"


def test_summarize_remoteshoot_photo() -> None:
    built = ["/chdkptp.sh", "-ec", '-eremoteshoot "/tmp/out" -jpg']
    assert _summarize_chdkptp_command(built) == "remoteshoot_photo"


def test_summarize_remoteshoot_live_view() -> None:
    built = ["/chdkptp.sh", "-ec", '-eremoteshoot "/tmp/lv" -jpg -view=1']
    assert _summarize_chdkptp_command(built) == "remoteshoot_live_view"


def test_pretty_argv_splits_luar_at_semicolons() -> None:
    lua = "local x=1; " + "; ".join(f"k{i}={i}" for i in range(40))  # >100 chars, many clauses
    cmd = ["/bin/chdkptp.sh", "-ec", f"-eluar {lua}"]
    out = _pretty_chdkptp_argv_log(cmd)
    assert "argv:" in out
    assert "[2] -eluar" in out
    assert out.count("\n") >= 6
    assert "k0=0" in out and "k39=39" in out
