from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.http import create_app  # type: ignore[import-not-found]


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
    assert "mode" in camera_status.json()

    capture = client.post("/api/capture/photo")
    assert capture.status_code == 200
    capture_payload = capture.json()
    assert capture_payload["source"] == "camera"
    assert capture_payload["file_path"].endswith(".jpg")

    solar_today = client.get("/api/solar/today")
    assert solar_today.status_code == 200
    solar_payload = solar_today.json()
    assert "sunrise" in solar_payload
    assert "golden_hour_morning_start" in solar_payload
    assert "astronomical_dusk" in solar_payload

    unknown_plan = client.get("/api/timelapse/plans/not-found")
    assert unknown_plan.status_code == 404

    plan_create = client.post(
        "/api/timelapse/plans",
        json={
            "interval_seconds": 60,
            "window_start_hour": 0,
            "window_end_hour": 23,
        },
    )
    assert plan_create.status_code == 200
    plan_payload = plan_create.json()
    plan_id = plan_payload["id"]
    assert plan_payload["active"] is False

    plan_start = client.post(f"/api/timelapse/plans/{plan_id}/start")
    assert plan_start.status_code == 200
    assert plan_start.json()["active"] is True

    plan_stop = client.post(f"/api/timelapse/plans/{plan_id}/stop")
    assert plan_stop.status_code == 200
    assert plan_stop.json()["active"] is False
