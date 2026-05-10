from __future__ import annotations

import logging


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s request_id=%(request_id)s")
    )
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def get_logger(name: str) -> logging.LoggerAdapter:
    base_logger = logging.getLogger(name)
    return logging.LoggerAdapter(base_logger, extra={"request_id": "-"})
