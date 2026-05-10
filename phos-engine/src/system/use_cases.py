from __future__ import annotations

from src.system.domain import SystemMetrics
from src.system.port import MetricsGateway


class GetSystemMetrics:
    def __init__(self, metrics_gateway: MetricsGateway) -> None:
        self._metrics_gateway = metrics_gateway

    def execute(self) -> SystemMetrics:
        return self._metrics_gateway.get_metrics()
