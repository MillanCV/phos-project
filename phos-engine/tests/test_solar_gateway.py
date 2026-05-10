from __future__ import annotations

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
