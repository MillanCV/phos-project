from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from src.domain.models import CaptureRecord, capture_record_from_path


class LocalStorageGateway:
    def __init__(self, metadata_file: Path) -> None:
        self._metadata_file = metadata_file
        self._metadata_file.parent.mkdir(parents=True, exist_ok=True)

    def register_capture(self, file_path: Path, source: str = "camera") -> CaptureRecord:
        record = capture_record_from_path(file_path, source=source)
        records = self._read_records()
        records.insert(
            0,
            {
                "id": record.id,
                "file_path": record.file_path,
                "captured_at": record.captured_at.isoformat(),
                "source": record.source,
            },
        )
        self._metadata_file.write_text(json.dumps(records[:500], indent=2), encoding="utf-8")
        return record

    def get_latest_capture(self) -> CaptureRecord | None:
        records = self._read_records()
        if not records:
            return None
        latest = records[0]
        return CaptureRecord(
            id=latest["id"],
            file_path=latest["file_path"],
            captured_at=datetime.fromisoformat(latest["captured_at"]).astimezone(timezone.utc),
            source=latest.get("source", "camera"),
        )

    def _read_records(self) -> list[dict[str, str]]:
        if not self._metadata_file.exists():
            return []
        try:
            payload = json.loads(self._metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return payload
