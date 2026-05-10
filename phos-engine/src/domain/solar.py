from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone


@dataclass(slots=True, frozen=True)
class SolarLocation:
    latitude: float
    longitude: float
    timezone_name: str
    name: str = "Phos Site"


@dataclass(slots=True)
class SolarWindow:
    day: date
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def daylight_seconds(self) -> float:
        return max(0.0, (self.sunset - self.sunrise).total_seconds())

    @property
    def night_seconds(self) -> float:
        return max(0.0, 86400.0 - self.daylight_seconds)
