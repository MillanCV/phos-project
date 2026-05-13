from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
import threading
import time

from src.camera.chdkptp.command_builder import build_exec_command
from src.shared.logging import get_logger


def _camera_command_log_mode() -> str:
    """PHOS_CAMERA_COMMAND_LOG: default full argv | 0=off | summary=compact."""
    raw = os.getenv("PHOS_CAMERA_COMMAND_LOG", "full").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return "off"
    if raw in ("full", "verbose", "all"):
        return "full"
    return "summary"


def _pretty_long_payload(payload: str, indent: str, chunk: int = 100) -> str:
    payload = payload.strip()
    if not payload:
        return ""
    if len(payload) <= chunk:
        return indent + payload
    return "\n".join(indent + payload[i : i + chunk] for i in range(0, len(payload), chunk))


def _pretty_lua_body(body: str, cont_indent: str) -> str:
    """Break one-line Lua at '; ' for readability (CHDK one-liners)."""
    body = body.strip()
    if not body:
        return ""
    if "; " in body and len(body) > 80:
        chunks = [c.strip() for c in body.split("; ") if c.strip()]
        if len(chunks) > 1:
            return "\n".join(cont_indent + c for c in chunks)
    return _pretty_long_payload(body, cont_indent, chunk=96)


def _pretty_chdkptp_argv_log(command: list[str]) -> str:
    """Multi-line argv for full logging: indexed args, long -eluar split at '; '."""
    if not command:
        return "  (empty)"
    lines: list[str] = ["  argv:", f"    [0] {command[0]}"]
    for idx, arg in enumerate(command[1:], start=1):
        if arg.startswith("-e") and len(arg) > 3:
            pl = arg[2:]
            if pl.startswith("luar ") and len(arg) > 100:
                lines.append(f"    [{idx}] -eluar")
                lines.append(_pretty_lua_body(pl[5:], "        "))
            elif len(arg) > 140:
                lines.append(f"    [{idx}] -e ({len(pl)} chars)")
                lines.append(_pretty_long_payload(pl, "        "))
            else:
                lines.append(f"    [{idx}] {arg}")
        elif len(arg) > 140:
            lines.append(f"    [{idx}] ({len(arg)} chars)")
            lines.append(_pretty_long_payload(arg, "        "))
        else:
            lines.append(f"    [{idx}] {arg}")
    return "\n".join(lines)


def _summarize_chdkptp_command(command: list[str]) -> str:
    """Short label for INFO logs (no full Lua)."""
    if len(command) >= 2 and any(a == "-elist" for a in command[1:]):
        return "elist"
    tail = " ".join(command[1:])
    if "return 'PHOS_OK'" in tail or 'return "PHOS_OK"' in tail:
        return "probe PHOS_OK"
    if "get_tv96()" in tail or ("PHOS:" in tail and "get_iso_real" in tail):
        return "lua manual_state"
    if "FLTABLE" in tail:
        return "lua zoom_focal_table"
    if "remoteshoot" in tail:
        # Photo / live view use chdkptp's remoteshoot, not -eluar Lua; do not label as "lua".
        if "-view=1" in tail:
            return "remoteshoot_live_view"
        return "remoteshoot_photo"
    if tail.startswith("-e") or "-e" in tail:
        # build_exec_command: -ec, -eluar…, -erec, …
        chunks: list[str] = []
        for a in command[1:]:
            if a.startswith("-e") and len(a) > 2:
                p = a[2:]
                if p.startswith("luar ") and len(p) > 72:
                    chunks.append(f"luar {p[5:68]}…")
                elif len(p) > 64:
                    chunks.append(f"{p[:61]}…")
                else:
                    chunks.append(p)
        return " | ".join(chunks) if chunks else tail[:120] + ("…" if len(tail) > 120 else "")
    return tail[:120] + ("…" if len(tail) > 120 else "")


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
        mode = _camera_command_log_mode()
        want_debug = self._log.logger.isEnabledFor(logging.DEBUG)
        summary = _summarize_chdkptp_command(command)
        for attempt in range(max_attempts):
            t0 = time.monotonic()
            if mode == "full":
                self._log.info(
                    "chdkptp exec start attempt=%s/%s timeout_s=%s\n%s",
                    attempt + 1,
                    max_attempts,
                    timeout_seconds,
                    _pretty_chdkptp_argv_log(command),
                )
            elif mode == "off" and want_debug:
                self._log.debug(
                    "chdkptp exec start attempt=%s/%s timeout_s=%s cmd=%s",
                    attempt + 1,
                    max_attempts,
                    timeout_seconds,
                    summary,
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
            st = (result.stderr or "").strip()
            tail = st[-900:].replace("\n", "\\n") if st else ""
            tail_on_error = f" stderr_tail={tail!r}" if tail and result.returncode != 0 else ""
            tail_full = f" stderr_tail={tail!r}" if tail else ""

            if mode == "full":
                self._log.info(
                    "chdkptp exec end attempt=%s/%s rc=%s elapsed_ms=%.0f stdout_chars=%s stderr_chars=%s%s",
                    attempt + 1,
                    max_attempts,
                    result.returncode,
                    elapsed_ms,
                    len(result.stdout or ""),
                    len(result.stderr or ""),
                    tail_full,
                )
            elif mode == "summary":
                self._log.info(
                    "chdkptp run cmd=%r rc=%s %.0fms out=%sb err=%sb attempt=%s/%s%s",
                    summary,
                    result.returncode,
                    elapsed_ms,
                    len(result.stdout or ""),
                    len(result.stderr or ""),
                    attempt + 1,
                    max_attempts,
                    tail_on_error,
                )
            elif want_debug:
                self._log.debug(
                    "chdkptp run cmd=%r rc=%s %.0fms out=%sb err=%sb attempt=%s/%s%s",
                    summary,
                    result.returncode,
                    elapsed_ms,
                    len(result.stdout or ""),
                    len(result.stderr or ""),
                    attempt + 1,
                    max_attempts,
                    tail_on_error,
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
