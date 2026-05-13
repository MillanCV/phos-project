from __future__ import annotations

import logging
import os
import sys
from typing import Any

from loguru import logger as loguru_logger

_PHOS_LOGURU_INSTALLED = False


def _stderr_colorize() -> bool:
    """ANSI / Loguru markup on by default; set PHOS_LOG_COLOR=0 to disable (e.g. piping to a file)."""
    raw = os.getenv("PHOS_LOG_COLOR", "").strip().lower()
    if raw in ("0", "false", "no", "off", "never"):
        return False
    return True


def _channel_plain_label(log_name: str) -> str:
    """Short tag without color (for PHOS_LOG_COLOR=0)."""
    if "chdkptp" in log_name:
        return "chdkptp"
    if log_name.startswith("phos.api"):
        return "api"
    if log_name.startswith("uvicorn"):
        return "uvicorn"
    if log_name.startswith("fastapi"):
        return "fastapi"
    if log_name.startswith("phos.camera"):
        return "camera"
    if log_name.startswith("phos."):
        return "phos"
    return "app"


def _channel_markup(log_name: str) -> str:
    """Loguru color tags (must be stitched into the format string, not passed via extra — extra values are escaped)."""
    if "chdkptp" in log_name:
        return "<magenta>chdkptp</magenta>"
    if log_name.startswith("phos.api"):
        return "<blue>api</blue>"
    if log_name.startswith("uvicorn"):
        return "<yellow>uvicorn</yellow>"
    if log_name.startswith("fastapi"):
        return "<green>fastapi</green>"
    if log_name.startswith("phos.camera"):
        return "<yellow>camera</yellow>"
    if log_name.startswith("phos."):
        return "<cyan>phos</cyan>"
    return "<white>app</white>"


def _phos_log_format(record: Any) -> str:
    """Build one line; markup in the returned string is colorized by Loguru (not via extra[...])."""
    log_name = record["extra"].get("log_name", "-")
    rid = record["extra"].get("request_id", "-")
    msg = str(record["message"])
    t = record["time"]
    ts = t.strftime("%Y-%m-%d %H:%M:%S") + f".{t.microsecond // 1000:03d}"
    lvl = record["level"].name
    if not _stderr_colorize():
        ch = _channel_plain_label(log_name)
        return f"{ts} | {lvl:<8} | {ch} | {rid} | {log_name} | {msg}\n"
    ch = _channel_markup(log_name)
    return (
        f"<green>{ts}</green> | "
        f"<level>{lvl:<8}</level> | "
        f"{ch} | "
        f"<white>{rid}</white> | "
        f"<dim>{log_name}</dim> | "
        f"{msg}\n"
    )


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


class InterceptHandler(logging.Handler):
    """Send stdlib logging records to Loguru (one sink, one format)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = "INFO"
        depth = 2
        frame = logging.currentframe()
        if frame is not None:
            frame = frame.f_back
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
        loguru_logger.bind(
            request_id=getattr(record, "request_id", "-"),
            log_name=record.name,
        ).opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _stdlib_level(name: str) -> int:
    n = name.strip().upper()
    if n in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return getattr(logging, n)
    return logging.INFO


def _detach_uvicorn_console_handlers() -> None:
    """Uvicorn installs its own access/error handlers (green INFO lines); force propagation to root → Loguru only."""
    for name in ("uvicorn.access", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True


def resync_uvicorn_log_handlers() -> None:
    """Uvicorn may attach handlers after import; call from FastAPI startup to avoid duplicate access lines."""
    _detach_uvicorn_console_handlers()


def _install_loguru_and_intercept() -> None:
    global _PHOS_LOGURU_INSTALLED
    if _PHOS_LOGURU_INSTALLED:
        return
    raw = os.getenv("PHOS_LOG_LEVEL", "DEBUG").strip().upper()
    lu_level = raw if raw in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") else "DEBUG"

    loguru_logger.remove()
    loguru_logger.configure(extra={"request_id": "-", "log_name": "-"})
    loguru_logger.add(
        sys.stderr,
        format=_phos_log_format,
        level=lu_level,
        colorize=_stderr_colorize(),
    )

    root = logging.getLogger()
    root.handlers.clear()
    handler = InterceptHandler()
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)
    root.setLevel(_stdlib_level(lu_level))

    _detach_uvicorn_console_handlers()

    _PHOS_LOGURU_INSTALLED = True


def configure_logging() -> None:
    _install_loguru_and_intercept()
    access_raw = os.getenv("PHOS_UVICORN_ACCESS_LOG", "1").strip().lower()
    access_off = access_raw in ("0", "false", "no", "off", "never")
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if access_off else logging.INFO)
    resync_uvicorn_log_handlers()


def get_logger(name: str) -> logging.LoggerAdapter:
    base_logger = logging.getLogger(name)
    return logging.LoggerAdapter(base_logger, extra={"request_id": "-"})
