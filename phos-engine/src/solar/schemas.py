from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class SolarWindowResponse(BaseModel):
    day: date
    astronomical_dawn: datetime | None
    nautical_dawn: datetime | None
    civil_dawn: datetime | None
    blue_hour_morning_start: datetime | None
    blue_hour_morning_end: datetime | None
    golden_hour_morning_start: datetime | None
    sunrise: datetime
    golden_hour_morning_end: datetime | None
    sunset: datetime
    golden_hour_evening_start: datetime | None
    golden_hour_evening_end: datetime | None
    blue_hour_evening_start: datetime | None
    blue_hour_evening_end: datetime | None
    civil_dusk: datetime | None
    nautical_dusk: datetime | None
    astronomical_dusk: datetime | None
    solar_noon: datetime
    daylight_hours: float
    night_hours: float
    calculated_at: datetime


class SolarRangeSummaryResponse(BaseModel):
    start_date: date
    end_date: date
    days: int
    sunrise_min: datetime
    sunrise_max: datetime
    sunset_min: datetime
    sunset_max: datetime
    daylight_min_hours: float
    daylight_max_hours: float
    daylight_avg_hours: float
    night_min_hours: float
    night_max_hours: float
    night_avg_hours: float
