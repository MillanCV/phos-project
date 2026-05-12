from __future__ import annotations

import json

from src.capture.gateway import LocalStorageGateway  # type: ignore[import-not-found]


def test_get_latest_capture_skips_nonexistent_files(tmp_path):
    metadata = tmp_path / "captures.json"
    missing = tmp_path / "missing.jpg"
    existing = tmp_path / "existing.jpg"
    existing.write_bytes(b"img")
    metadata.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "file_path": str(missing),
                    "captured_at": "2026-05-12T11:00:00+00:00",
                    "source": "camera",
                },
                {
                    "id": "2",
                    "file_path": str(existing),
                    "captured_at": "2026-05-12T11:01:00+00:00",
                    "source": "camera",
                },
            ]
        ),
        encoding="utf-8",
    )

    gateway = LocalStorageGateway(metadata_file=metadata)
    latest = gateway.get_latest_capture()

    assert latest is not None
    assert latest.id == "2"
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["id"] == "2"
