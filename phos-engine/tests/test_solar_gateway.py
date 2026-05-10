from __future__ import annotations

import json
from datetime import datetime, timezone
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from src.domain.solar import SolarLocation
from src.infrastructure.astral_solar_gateway import AstralSolarGateway


def test_solar_gateway_returns_window_and_persists_cache():
    with TemporaryDirectory() as tmp_dir:
        cache_file = Path(tmp_dir) / "solar_cache.json"
        gateway = AstralSolarGateway(
            location=SolarLocation(
                latitude=40.4168,
                longitude=-3.7038,
                timezone_name="Europe/Madrid",
                name="Madrid",
            ),
            cache_file=cache_file,
        )

        window = gateway.get_window(date(2026, 6, 1))

        assert window.sunrise < window.sunset
        assert window.civil_dawn is not None
        assert window.civil_dusk is not None
        assert window.golden_hour_morning_start is not None
        assert window.golden_hour_evening_end is not None
        assert cache_file.exists()


def test_solar_gateway_range_size():
    with TemporaryDirectory() as tmp_dir:
        cache_file = Path(tmp_dir) / "solar_cache.json"
        gateway = AstralSolarGateway(
            location=SolarLocation(
                latitude=40.4168,
                longitude=-3.7038,
                timezone_name="Europe/Madrid",
                name="Madrid",
            ),
            cache_file=cache_file,
        )

        windows = gateway.get_range(start_date=date(2026, 6, 1), days=5)
        assert len(windows) == 5


def test_solar_gateway_refreshes_legacy_cache_entries():
    with TemporaryDirectory() as tmp_dir:
        cache_file = Path(tmp_dir) / "solar_cache.json"
        cache_file.write_text(
            json.dumps(
                {
                    "2026-06-01": {
                        "day": "2026-06-01",
                        "sunrise": "2026-06-01T06:45:00+02:00",
                        "sunset": "2026-06-01T21:35:00+02:00",
                        "solar_noon": "2026-06-01T14:10:00+02:00",
                        "calculated_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
            ),
            encoding="utf-8",
        )
        gateway = AstralSolarGateway(
            location=SolarLocation(
                latitude=40.4168,
                longitude=-3.7038,
                timezone_name="Europe/Madrid",
                name="Madrid",
            ),
            cache_file=cache_file,
        )

        window = gateway.get_window(date(2026, 6, 1))
        assert window.civil_dawn is not None
        assert window.golden_hour_morning_start is not None
