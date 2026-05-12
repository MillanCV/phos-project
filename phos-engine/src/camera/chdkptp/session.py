from __future__ import annotations

import subprocess
from dataclasses import dataclass

from src.camera.chdkptp.command_builder import build_exec_command


@dataclass(slots=True, frozen=True)
class ChdkptpSessionResult:
    command: list[str]
    stdout: str
    stderr: str
    returncode: int


class ChdkptpSession:
    def __init__(self, chdkptp_bin: str) -> None:
        self._chdkptp_bin = chdkptp_bin

    def run(self, commands: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        normalized = [item.strip() for item in commands]
        needs_connect = "c" not in normalized and "connect" not in normalized
        effective_commands = ["c", *commands] if needs_connect else commands
        command = build_exec_command(self._chdkptp_bin, effective_commands)
        return self._run_command(command=command, timeout_seconds=timeout_seconds)

    def run_cli(self, args: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        command = [self._chdkptp_bin, *args]
        return self._run_command(command=command, timeout_seconds=timeout_seconds)

    @staticmethod
    def _run_command(command: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        return ChdkptpSessionResult(
            command=command,
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode,
        )
