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
    status_payload = camera_status.json()
    assert "connection" in status_payload
    assert "mode" in status_payload
    assert "chdkptp_available" in status_payload
    assert "camera_session_state" in status_payload
    assert "last_successful_command_at" in status_payload
    assert "last_command_duration_ms" in status_payload

    camera_presets = client.get("/api/camera/presets")
    assert camera_presets.status_code == 200
    presets_payload = camera_presets.json()
    assert isinstance(presets_payload, list)
    assert len(presets_payload) >= 1
    first_preset = presets_payload[0]
    assert "name" in first_preset
    assert "description" in first_preset
    assert "timeout_seconds" in first_preset

    run_preset = client.post(f"/api/camera/presets/{first_preset['name']}/run")
    assert run_preset.status_code == 200
    run_payload = run_preset.json()
    assert run_payload["profile_name"] == first_preset["name"]
    assert "state" in run_payload

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
