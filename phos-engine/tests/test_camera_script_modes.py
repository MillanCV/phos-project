from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.http import create_app  # type: ignore[import-not-found]


def test_camera_script_run_and_status(isolated_data_dir, monkeypatch):
    monkeypatch.setenv("PHOS_CAMERA_MOCK", "true")
    monkeypatch.setenv("PHOS_SOLAR_CACHE_DAYS", "0")
    app = create_app()
    client = TestClient(app)

    run = client.post(
        "/api/camera/scripts/run",
        json={
            "name": "lightning-demo",
            "commands": ["rec", "lua print('ok')"],
            "timeout_seconds": 60,
            "expected_artifacts": [],
        },
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["state"] == "completed"
    run_id = payload["run_id"]

    status = client.get(f"/api/camera/scripts/{run_id}")
    assert status.status_code == 200
    assert status.json()["run_id"] == run_id


def test_lightning_and_motion_sessions_contract(isolated_data_dir, monkeypatch):
    monkeypatch.setenv("PHOS_CAMERA_MOCK", "true")
    monkeypatch.setenv("PHOS_SOLAR_CACHE_DAYS", "0")
    app = create_app()
    client = TestClient(app)

    lightning = client.post(
        "/api/lightning/sessions",
        json={
            "profile_name": "lightning",
            "commands": ["rec", "lua print('lightning')"],
            "timeout_seconds": 30,
        },
    )
    assert lightning.status_code == 200
    lightning_payload = lightning.json()
    assert lightning_payload["profile_name"] == "lightning"

    motion = client.post(
        "/api/motion/sessions",
        json={
            "profile_name": "motion",
            "commands": ["rec", "lua print('motion')"],
            "timeout_seconds": 30,
        },
    )
    assert motion.status_code == 200
    motion_payload = motion.json()
    assert motion_payload["profile_name"] == "motion"
