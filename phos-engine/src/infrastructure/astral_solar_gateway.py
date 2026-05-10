from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun

from src.domain.solar import SolarLocation, SolarWindow


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
            return self._cache[key]

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
        return SolarWindow(day=on_date, sunrise=result["sunrise"], sunset=result["sunset"], solar_noon=result["noon"])

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
                cache[key] = SolarWindow(
                    day=date.fromisoformat(value["day"]),
                    sunrise=datetime.fromisoformat(value["sunrise"]),
                    sunset=datetime.fromisoformat(value["sunset"]),
                    solar_noon=datetime.fromisoformat(value["solar_noon"]),
                    calculated_at=datetime.fromisoformat(value["calculated_at"]),
                )
            except (KeyError, ValueError, TypeError):
                continue
        return cache

    def _save_cache(self) -> None:
        serialized = {
            key: {
                **asdict(value),
                "day": value.day.isoformat(),
                "sunrise": value.sunrise.isoformat(),
                "sunset": value.sunset.isoformat(),
                "solar_noon": value.solar_noon.isoformat(),
                "calculated_at": value.calculated_at.isoformat(),
            }
            for key, value in self._cache.items()
        }
        self._cache_file.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
