from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.domain.solar import SolarWindow  # type: ignore[import-not-found]
from src.interfaces.http.app import _to_solar_summary  # type: ignore[import-not-found]


def test_solar_window_daylight_and_night_hours_sum_to_24():
    tz = ZoneInfo("Europe/Madrid")
    window = SolarWindow(
        day=date(2026, 6, 1),
        sunrise=datetime(2026, 6, 1, 6, 45, tzinfo=tz),
        sunset=datetime(2026, 6, 1, 21, 33, tzinfo=tz),
        solar_noon=datetime(2026, 6, 1, 14, 9, tzinfo=tz),
    )
    total_hours = (window.daylight_seconds + window.night_seconds) / 3600
    assert round(total_hours, 3) == 24.0


def test_solar_range_summary_contains_min_max_and_averages():
    tz = ZoneInfo("Europe/Madrid")
    windows = [
        SolarWindow(
            day=date(2026, 6, 1),
            sunrise=datetime(2026, 6, 1, 6, 45, tzinfo=tz),
            sunset=datetime(2026, 6, 1, 21, 33, tzinfo=tz),
            solar_noon=datetime(2026, 6, 1, 14, 9, tzinfo=tz),
        ),
        SolarWindow(
            day=date(2026, 6, 2),
            sunrise=datetime(2026, 6, 2, 6, 44, tzinfo=tz),
            sunset=datetime(2026, 6, 2, 21, 34, tzinfo=tz),
            solar_noon=datetime(2026, 6, 2, 14, 9, tzinfo=tz),
        ),
    ]

    summary = _to_solar_summary(windows)

    assert summary.days == 2
    assert summary.sunrise_min.hour == 6
    assert summary.sunset_max.hour == 21
    assert round(summary.daylight_avg_hours + summary.night_avg_hours, 3) == 24.0
