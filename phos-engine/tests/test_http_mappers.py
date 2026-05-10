from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.solar.domain import PhotoWindows, SolarWindow, TwilightTimes
from src.solar.mappers import to_solar_response


def test_to_solar_response_preserves_extended_windows():
    tz = ZoneInfo("Europe/Madrid")
    window = SolarWindow(
        day=date(2026, 6, 1),
        sunrise=datetime(2026, 6, 1, 6, 45, tzinfo=tz),
        sunset=datetime(2026, 6, 1, 21, 33, tzinfo=tz),
        solar_noon=datetime(2026, 6, 1, 14, 9, tzinfo=tz),
        twilight=TwilightTimes(
            civil_dawn=datetime(2026, 6, 1, 6, 10, tzinfo=tz),
            civil_dusk=datetime(2026, 6, 1, 22, 5, tzinfo=tz),
            nautical_dawn=datetime(2026, 6, 1, 5, 30, tzinfo=tz),
            nautical_dusk=datetime(2026, 6, 1, 22, 45, tzinfo=tz),
        ),
        photo_windows=PhotoWindows(
            golden_hour_morning_start=datetime(2026, 6, 1, 6, 20, tzinfo=tz),
            golden_hour_morning_end=datetime(2026, 6, 1, 7, 10, tzinfo=tz),
            blue_hour_evening_start=datetime(2026, 6, 1, 21, 50, tzinfo=tz),
            blue_hour_evening_end=datetime(2026, 6, 1, 22, 10, tzinfo=tz),
        ),
    )

    result = to_solar_response(window)

    assert result.day == date(2026, 6, 1)
    assert result.civil_dawn is not None
    assert result.golden_hour_morning_start is not None
    assert result.blue_hour_evening_end is not None
    assert round(result.daylight_hours + result.night_hours, 3) == 24.0
