from __future__ import annotations

from typing import Protocol

from src.system.domain import SystemMetrics


class MetricsGateway(Protocol):
    def get_metrics(self) -> SystemMetrics: ...
