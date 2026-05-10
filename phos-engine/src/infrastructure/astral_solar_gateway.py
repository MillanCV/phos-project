from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import SunDirection, dawn, dusk, sun, time_at_elevation

from src.domain.solar import PhotoWindows, SolarLocation, SolarWindow, TwilightTimes


class AstralSolarGateway:
    def __init__(self, location: SolarLocation, cache_file: Path) -> None:
        self._location = location
        self._cache_file = cache_file
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, SolarWindow] = self._load_cache()

    def prime_cache(self, days: int) -> None:
        if days <= 0:
            return
        today = datetime.now(ZoneInfo(self._location.timezone_name)).date()
        self.get_range(today, days)

    def get_window(self, on_date: date) -> SolarWindow:
        key = on_date.isoformat()
        if key in self._cache:
            cached = self._cache[key]
            if not self._has_extended_windows(cached):
                refreshed = self._calculate_window(on_date)
                self._cache[key] = refreshed
                self._save_cache()
                return refreshed
            return cached

        window = self._calculate_window(on_date)
        self._cache[key] = window
        self._save_cache()
        return window

    def get_range(self, start_date: date, days: int) -> list[SolarWindow]:
        if days <= 0:
            return []
        if days > 366:
            days = 366

        windows = [self.get_window(start_date + timedelta(days=offset)) for offset in range(days)]
        self._save_cache()
        return windows

    def _calculate_window(self, on_date: date) -> SolarWindow:
        tz = ZoneInfo(self._location.timezone_name)
        location = LocationInfo(
            name=self._location.name,
            region="Phos",
            timezone=self._location.timezone_name,
            latitude=self._location.latitude,
            longitude=self._location.longitude,
        )
        result = sun(location.observer, date=on_date, tzinfo=tz)
        sunrise = result["sunrise"]
        sunset = result["sunset"]

        civil_dawn = self._safe_time(lambda: dawn(location.observer, date=on_date, tzinfo=tz, depression=6))
        civil_dusk = self._safe_time(lambda: dusk(location.observer, date=on_date, tzinfo=tz, depression=6))
        nautical_dawn = self._safe_time(lambda: dawn(location.observer, date=on_date, tzinfo=tz, depression=12))
        nautical_dusk = self._safe_time(lambda: dusk(location.observer, date=on_date, tzinfo=tz, depression=12))
        astronomical_dawn = self._safe_time(lambda: dawn(location.observer, date=on_date, tzinfo=tz, depression=18))
        astronomical_dusk = self._safe_time(lambda: dusk(location.observer, date=on_date, tzinfo=tz, depression=18))

        golden_morning_start = self._safe_time(
            lambda: time_at_elevation(
                location.observer, -4.0, date=on_date, direction=SunDirection.RISING, tzinfo=tz, with_refraction=True
            )
        )
        golden_morning_end = self._safe_time(
            lambda: time_at_elevation(
                location.observer, 6.0, date=on_date, direction=SunDirection.RISING, tzinfo=tz, with_refraction=True
            )
        )
        golden_evening_start = self._safe_time(
            lambda: time_at_elevation(
                location.observer, 6.0, date=on_date, direction=SunDirection.SETTING, tzinfo=tz, with_refraction=True
            )
        )
        golden_evening_end = self._safe_time(
            lambda: time_at_elevation(
                location.observer, -4.0, date=on_date, direction=SunDirection.SETTING, tzinfo=tz, with_refraction=True
            )
        )

        blue_morning_start = civil_dawn
        blue_morning_end = golden_morning_start
        blue_evening_start = golden_evening_end
        blue_evening_end = civil_dusk

        return SolarWindow(
            day=on_date,
            sunrise=sunrise,
            sunset=sunset,
            solar_noon=result["noon"],
            twilight=TwilightTimes(
                civil_dawn=civil_dawn,
                civil_dusk=civil_dusk,
                nautical_dawn=nautical_dawn,
                nautical_dusk=nautical_dusk,
                astronomical_dawn=astronomical_dawn,
                astronomical_dusk=astronomical_dusk,
            ),
            photo_windows=PhotoWindows(
                golden_hour_morning_start=golden_morning_start,
                golden_hour_morning_end=golden_morning_end,
                golden_hour_evening_start=golden_evening_start,
                golden_hour_evening_end=golden_evening_end,
                blue_hour_morning_start=blue_morning_start,
                blue_hour_morning_end=blue_morning_end,
                blue_hour_evening_start=blue_evening_start,
                blue_hour_evening_end=blue_evening_end,
            ),
        )

    def _load_cache(self) -> dict[str, SolarWindow]:
        if not self._cache_file.exists():
            return {}

        try:
            payload = json.loads(self._cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

        if not isinstance(payload, dict):
            return {}

        cache: dict[str, SolarWindow] = {}
        for key, value in payload.items():
            if not isinstance(value, dict):
                continue
            try:
                cache[key] = self._deserialize_window(value)
            except (KeyError, ValueError, TypeError):
                continue
        return cache

    def _save_cache(self) -> None:
        serialized = {key: self._serialize_window(value) for key, value in self._cache.items()}
        self._cache_file.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_time(fn):
        try:
            return fn()
        except ValueError:
            return None

    @staticmethod
    def _has_extended_windows(window: SolarWindow) -> bool:
        extended_fields = (
            window.civil_dawn,
            window.civil_dusk,
            window.nautical_dawn,
            window.nautical_dusk,
            window.astronomical_dawn,
            window.astronomical_dusk,
            window.golden_hour_morning_start,
            window.golden_hour_morning_end,
            window.golden_hour_evening_start,
            window.golden_hour_evening_end,
            window.blue_hour_morning_start,
            window.blue_hour_morning_end,
            window.blue_hour_evening_start,
            window.blue_hour_evening_end,
        )
        return any(field is not None for field in extended_fields)

    @staticmethod
    def _serialize_window(window: SolarWindow) -> dict[str, object]:
        payload = asdict(window)
        return AstralSolarGateway._serialize_value(payload)

    @staticmethod
    def _serialize_value(value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): AstralSolarGateway._serialize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [AstralSolarGateway._serialize_value(item) for item in value]
        return value

    @staticmethod
    def _deserialize_window(data: dict[str, object]) -> SolarWindow:
        def parse_dt(key: str) -> datetime | None:
            raw = data.get(key)
            return datetime.fromisoformat(str(raw)) if raw else None

        twilight_data = data.get("twilight")
        if isinstance(twilight_data, dict):
            twilight = TwilightTimes(
                civil_dawn=(
                    datetime.fromisoformat(str(twilight_data["civil_dawn"])) if twilight_data.get("civil_dawn") else None
                ),
                civil_dusk=(
                    datetime.fromisoformat(str(twilight_data["civil_dusk"])) if twilight_data.get("civil_dusk") else None
                ),
                nautical_dawn=(
                    datetime.fromisoformat(str(twilight_data["nautical_dawn"]))
                    if twilight_data.get("nautical_dawn")
                    else None
                ),
                nautical_dusk=(
                    datetime.fromisoformat(str(twilight_data["nautical_dusk"]))
                    if twilight_data.get("nautical_dusk")
                    else None
                ),
                astronomical_dawn=(
                    datetime.fromisoformat(str(twilight_data["astronomical_dawn"]))
                    if twilight_data.get("astronomical_dawn")
                    else None
                ),
                astronomical_dusk=(
                    datetime.fromisoformat(str(twilight_data["astronomical_dusk"]))
                    if twilight_data.get("astronomical_dusk")
                    else None
                ),
            )
        else:
            # Legacy cache format compatibility.
            twilight = TwilightTimes(
                civil_dawn=parse_dt("civil_dawn"),
                civil_dusk=parse_dt("civil_dusk"),
                nautical_dawn=parse_dt("nautical_dawn"),
                nautical_dusk=parse_dt("nautical_dusk"),
                astronomical_dawn=parse_dt("astronomical_dawn"),
                astronomical_dusk=parse_dt("astronomical_dusk"),
            )

        photo_windows_data = data.get("photo_windows")
        if isinstance(photo_windows_data, dict):
            photo_windows = PhotoWindows(
                golden_hour_morning_start=(
                    datetime.fromisoformat(str(photo_windows_data["golden_hour_morning_start"]))
                    if photo_windows_data.get("golden_hour_morning_start")
                    else None
                ),
                golden_hour_morning_end=(
                    datetime.fromisoformat(str(photo_windows_data["golden_hour_morning_end"]))
                    if photo_windows_data.get("golden_hour_morning_end")
                    else None
                ),
                golden_hour_evening_start=(
                    datetime.fromisoformat(str(photo_windows_data["golden_hour_evening_start"]))
                    if photo_windows_data.get("golden_hour_evening_start")
                    else None
                ),
                golden_hour_evening_end=(
                    datetime.fromisoformat(str(photo_windows_data["golden_hour_evening_end"]))
                    if photo_windows_data.get("golden_hour_evening_end")
                    else None
                ),
                blue_hour_morning_start=(
                    datetime.fromisoformat(str(photo_windows_data["blue_hour_morning_start"]))
                    if photo_windows_data.get("blue_hour_morning_start")
                    else None
                ),
                blue_hour_morning_end=(
                    datetime.fromisoformat(str(photo_windows_data["blue_hour_morning_end"]))
                    if photo_windows_data.get("blue_hour_morning_end")
                    else None
                ),
                blue_hour_evening_start=(
                    datetime.fromisoformat(str(photo_windows_data["blue_hour_evening_start"]))
                    if photo_windows_data.get("blue_hour_evening_start")
                    else None
                ),
                blue_hour_evening_end=(
                    datetime.fromisoformat(str(photo_windows_data["blue_hour_evening_end"]))
                    if photo_windows_data.get("blue_hour_evening_end")
                    else None
                ),
            )
        else:
            photo_windows = PhotoWindows(
                golden_hour_morning_start=parse_dt("golden_hour_morning_start"),
                golden_hour_morning_end=parse_dt("golden_hour_morning_end"),
                golden_hour_evening_start=parse_dt("golden_hour_evening_start"),
                golden_hour_evening_end=parse_dt("golden_hour_evening_end"),
                blue_hour_morning_start=parse_dt("blue_hour_morning_start"),
                blue_hour_morning_end=parse_dt("blue_hour_morning_end"),
                blue_hour_evening_start=parse_dt("blue_hour_evening_start"),
                blue_hour_evening_end=parse_dt("blue_hour_evening_end"),
            )

        return SolarWindow(
            day=date.fromisoformat(str(data.get("day") or data["on_date"])),
            sunrise=datetime.fromisoformat(str(data["sunrise"])),
            sunset=datetime.fromisoformat(str(data["sunset"])),
            solar_noon=datetime.fromisoformat(str(data["solar_noon"])),
            twilight=twilight,
            photo_windows=photo_windows,
            calculated_at=datetime.fromisoformat(str(data["calculated_at"])),
        )
