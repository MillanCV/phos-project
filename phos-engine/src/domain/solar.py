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
    civil_dawn: datetime | None = None
    civil_dusk: datetime | None = None
    nautical_dawn: datetime | None = None
    nautical_dusk: datetime | None = None
    astronomical_dawn: datetime | None = None
    astronomical_dusk: datetime | None = None
    golden_hour_morning_start: datetime | None = None
    golden_hour_morning_end: datetime | None = None
    golden_hour_evening_start: datetime | None = None
    golden_hour_evening_end: datetime | None = None
    blue_hour_morning_start: datetime | None = None
    blue_hour_morning_end: datetime | None = None
    blue_hour_evening_start: datetime | None = None
    blue_hour_evening_end: datetime | None = None
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def daylight_seconds(self) -> float:
        return max(0.0, (self.sunset - self.sunrise).total_seconds())

    @property
    def night_seconds(self) -> float:
        return max(0.0, 86400.0 - self.daylight_seconds)
