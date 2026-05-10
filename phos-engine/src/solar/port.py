from __future__ import annotations

from datetime import date
from typing import Protocol

from src.solar.domain import SolarDay


class SolarGateway(Protocol):
    def get_window(self, on_date: date) -> SolarDay: ...

    def get_range(self, start_date: date, days: int) -> list[SolarDay]: ...

    def prime_cache(self, days: int) -> None: ...
