from __future__ import annotations

from fastapi import HTTPException

from src.interfaces.http.schemas.solar import SolarRangeSummaryResponse, SolarWindowResponse


def to_solar_response(window) -> SolarWindowResponse:
    return SolarWindowResponse(
        day=window.day,
        astronomical_dawn=window.astronomical_dawn,
        nautical_dawn=window.nautical_dawn,
        civil_dawn=window.civil_dawn,
        blue_hour_morning_start=window.blue_hour_morning_start,
        blue_hour_morning_end=window.blue_hour_morning_end,
        golden_hour_morning_start=window.golden_hour_morning_start,
        sunrise=window.sunrise,
        golden_hour_morning_end=window.golden_hour_morning_end,
        sunset=window.sunset,
        golden_hour_evening_start=window.golden_hour_evening_start,
        golden_hour_evening_end=window.golden_hour_evening_end,
        blue_hour_evening_start=window.blue_hour_evening_start,
        blue_hour_evening_end=window.blue_hour_evening_end,
        civil_dusk=window.civil_dusk,
        nautical_dusk=window.nautical_dusk,
        astronomical_dusk=window.astronomical_dusk,
        solar_noon=window.solar_noon,
        daylight_hours=round(window.daylight_seconds / 3600, 3),
        night_hours=round(window.night_seconds / 3600, 3),
        calculated_at=window.calculated_at,
    )


def to_solar_summary(windows) -> SolarRangeSummaryResponse:
    if not windows:
        raise HTTPException(status_code=404, detail="no solar windows available")

    daylight_hours = [window.daylight_seconds / 3600 for window in windows]
    night_hours = [window.night_seconds / 3600 for window in windows]
    return SolarRangeSummaryResponse(
        start_date=windows[0].day,
        end_date=windows[-1].day,
        days=len(windows),
        sunrise_min=min(window.sunrise for window in windows),
        sunrise_max=max(window.sunrise for window in windows),
        sunset_min=min(window.sunset for window in windows),
        sunset_max=max(window.sunset for window in windows),
        daylight_min_hours=round(min(daylight_hours), 3),
        daylight_max_hours=round(max(daylight_hours), 3),
        daylight_avg_hours=round(sum(daylight_hours) / len(daylight_hours), 3),
        night_min_hours=round(min(night_hours), 3),
        night_max_hours=round(max(night_hours), 3),
        night_avg_hours=round(sum(night_hours) / len(night_hours), 3),
    )
