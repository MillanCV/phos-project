from __future__ import annotations

from fastapi.testclient import TestClient

from src.interfaces.http.app import create_app


def test_http_contract_endpoints(isolated_data_dir, monkeypatch):
    monkeypatch.setenv("PHOS_CAMERA_MOCK", "true")
    monkeypatch.setenv("PHOS_SOLAR_CACHE_DAYS", "0")
    app = create_app()
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    camera_status = client.get("/api/camera/status")
    assert camera_status.status_code == 200
    assert "connection" in camera_status.json()

    solar_today = client.get("/api/solar/today")
    assert solar_today.status_code == 200
    solar_payload = solar_today.json()
    assert "sunrise" in solar_payload
    assert "golden_hour_morning_start" in solar_payload
    assert "astronomical_dusk" in solar_payload

    unknown_plan = client.get("/api/timelapse/plans/not-found")
    assert unknown_plan.status_code == 404
