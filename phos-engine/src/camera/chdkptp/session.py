from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
import threading
import time

from src.camera.chdkptp.command_builder import build_exec_command
from src.shared.logging import get_logger


def _camera_command_log_info() -> bool:
    """When true, log every chdkptp invocation at INFO (see PHOS_CAMERA_COMMAND_LOG)."""
    return os.getenv("PHOS_CAMERA_COMMAND_LOG", "").lower() in ("1", "true", "yes", "info")


def _format_chdkptp_argv(command: list[str], max_arg_len: int = 2400) -> str:
    """Single-line summary for logs; truncates long -eluar… payloads."""
    parts: list[str] = []
    for arg in command:
        if len(arg) > max_arg_len:
            parts.append(f"{arg[:max_arg_len]}…({len(arg)} chars)")
        else:
            parts.append(arg)
    return " ".join(parts)


@dataclass(slots=True, frozen=True)
class ChdkptpSessionResult:
    command: list[str]
    stdout: str
    stderr: str
    returncode: int


class ChdkptpSession:
    def __init__(self, chdkptp_bin: str) -> None:
        self._chdkptp_bin = chdkptp_bin
        self._command_lock = threading.Lock()
        self._log = get_logger("phos.camera.chdkptp.session")

    def run(self, commands: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        normalized = [item.strip() for item in commands]
        needs_connect = "c" not in normalized and "connect" not in normalized
        effective_commands = ["c", *commands] if needs_connect else commands
        command = build_exec_command(self._chdkptp_bin, effective_commands)
        return self._run_command(command=command, timeout_seconds=timeout_seconds)

    def run_cli(self, args: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        command = [self._chdkptp_bin, *args]
        return self._run_command(command=command, timeout_seconds=timeout_seconds)

    def _run_command(self, command: list[str], timeout_seconds: int) -> ChdkptpSessionResult:
        max_attempts = 3
        want_info = _camera_command_log_info()
        want_debug = self._log.logger.isEnabledFor(logging.DEBUG)
        for attempt in range(max_attempts):
            t0 = time.monotonic()
            if want_info or want_debug:
                self._log.log(
                    logging.INFO if want_info else logging.DEBUG,
                    "camera chdkptp exec start attempt=%s/%s timeout_s=%s argv=%s",
                    attempt + 1,
                    max_attempts,
                    timeout_seconds,
                    _format_chdkptp_argv(command),
                )
            with self._command_lock:
                try:
                    process = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=timeout_seconds,
                    )
                    result = ChdkptpSessionResult(
                        command=command,
                        stdout=process.stdout,
                        stderr=process.stderr,
                        returncode=process.returncode,
                    )
                except subprocess.TimeoutExpired as exc:
                    stderr = (exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else exc.stderr) or ""
                    stdout = (exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else exc.stdout) or ""
                    timeout_msg = f"command timed out after {timeout_seconds}s"
                    merged_stderr = f"{stderr}\n{timeout_msg}".strip()
                    result = ChdkptpSessionResult(
                        command=command,
                        stdout=stdout,
                        stderr=merged_stderr,
                        returncode=124,
                    )

            elapsed_ms = (time.monotonic() - t0) * 1000
            if want_info or want_debug:
                st = (result.stderr or "").strip()
                tail = st[-900:].replace("\n", "\\n") if st else ""
                self._log.log(
                    logging.INFO if want_info else logging.DEBUG,
                    "camera chdkptp exec end attempt=%s/%s rc=%s elapsed_ms=%.0f stdout_chars=%s stderr_chars=%s%s",
                    attempt + 1,
                    max_attempts,
                    result.returncode,
                    elapsed_ms,
                    len(result.stdout or ""),
                    len(result.stderr or ""),
                    f" stderr_tail={tail!r}" if tail else "",
                )

            if attempt < max_attempts - 1 and self._is_retryable_busy_error(result):
                # Give libusb/PTP a small settle window before retrying.
                time.sleep(0.2 * (attempt + 1))
                continue
            return result

    @staticmethod
    def _is_retryable_busy_error(result: ChdkptpSessionResult) -> bool:
        if result.returncode == 0:
            return False
        output = "\n".join(item for item in [result.stdout, result.stderr] if item).lower()
        return (
            "device or resource busy" in output
            or "usb_ptp_device_reset" in output
            or "usb_ptp_get_device_status" in output
        )
