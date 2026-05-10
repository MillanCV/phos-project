from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone


@dataclass(slots=True, frozen=True)
class SolarLocation:
    latitude: float
    longitude: float
    timezone_name: str
    name: str = "Phos Site"


@dataclass(slots=True, frozen=True)
class TwilightTimes:
    civil_dawn: datetime | None = None
    civil_dusk: datetime | None = None
    nautical_dawn: datetime | None = None
    nautical_dusk: datetime | None = None
    astronomical_dawn: datetime | None = None
    astronomical_dusk: datetime | None = None


@dataclass(slots=True, frozen=True)
class PhotoWindows:
    golden_hour_morning_start: datetime | None = None
    golden_hour_morning_end: datetime | None = None
    golden_hour_evening_start: datetime | None = None
    golden_hour_evening_end: datetime | None = None
    blue_hour_morning_start: datetime | None = None
    blue_hour_morning_end: datetime | None = None
    blue_hour_evening_start: datetime | None = None
    blue_hour_evening_end: datetime | None = None


@dataclass(slots=True, frozen=True)
class SolarDay:
    day: date
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    twilight: TwilightTimes = field(default_factory=TwilightTimes)
    photo_windows: PhotoWindows = field(default_factory=PhotoWindows)
    # Infrastructure timestamp kept here temporarily to avoid API breakage.
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def on_date(self) -> date:
        return self.day

    @property
    def daylight_seconds(self) -> float:
        return max(0.0, (self.sunset - self.sunrise).total_seconds())

    @property
    def night_seconds(self) -> float:
        return max(0.0, 86400.0 - self.daylight_seconds)

    @property
    def civil_dawn(self) -> datetime | None:
        return self.twilight.civil_dawn

    @property
    def civil_dusk(self) -> datetime | None:
        return self.twilight.civil_dusk

    @property
    def nautical_dawn(self) -> datetime | None:
        return self.twilight.nautical_dawn

    @property
    def nautical_dusk(self) -> datetime | None:
        return self.twilight.nautical_dusk

    @property
    def astronomical_dawn(self) -> datetime | None:
        return self.twilight.astronomical_dawn

    @property
    def astronomical_dusk(self) -> datetime | None:
        return self.twilight.astronomical_dusk

    @property
    def golden_hour_morning_start(self) -> datetime | None:
        return self.photo_windows.golden_hour_morning_start

    @property
    def golden_hour_morning_end(self) -> datetime | None:
        return self.photo_windows.golden_hour_morning_end

    @property
    def golden_hour_evening_start(self) -> datetime | None:
        return self.photo_windows.golden_hour_evening_start

    @property
    def golden_hour_evening_end(self) -> datetime | None:
        return self.photo_windows.golden_hour_evening_end

    @property
    def blue_hour_morning_start(self) -> datetime | None:
        return self.photo_windows.blue_hour_morning_start

    @property
    def blue_hour_morning_end(self) -> datetime | None:
        return self.photo_windows.blue_hour_morning_end

    @property
    def blue_hour_evening_start(self) -> datetime | None:
        return self.photo_windows.blue_hour_evening_start

    @property
    def blue_hour_evening_end(self) -> datetime | None:
        return self.photo_windows.blue_hour_evening_end


# Backward-compatible name while migrating modules.
SolarWindow = SolarDay
