from __future__ import annotations

from datetime import date

from src.application.ports import SolarGateway
from src.domain.solar import SolarWindow


class GetSolarWindow:
    def __init__(self, solar_gateway: SolarGateway) -> None:
        self._solar_gateway = solar_gateway

    def execute(self, on_date: date) -> SolarWindow:
        return self._solar_gateway.get_window(on_date)


class GetSolarRange:
    def __init__(self, solar_gateway: SolarGateway) -> None:
        self._solar_gateway = solar_gateway

    def execute(self, start_date: date, days: int) -> list[SolarWindow]:
        return self._solar_gateway.get_range(start_date, days)
