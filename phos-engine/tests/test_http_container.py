from __future__ import annotations

from src.interfaces.http.app import create_app


def test_app_bootstraps_container_and_routes(isolated_data_dir, monkeypatch):
    monkeypatch.setenv("PHOS_CAMERA_MOCK", "true")
    monkeypatch.setenv("PHOS_SOLAR_CACHE_DAYS", "0")
    app = create_app()

    assert hasattr(app.state, "container")
    paths = {route.path for route in app.routes}
    assert "/api/health" in paths
    assert "/api/solar/today" in paths
    assert "/api/timelapse/plans/{plan_id}" in paths
