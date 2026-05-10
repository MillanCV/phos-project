from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(slots=True)
class CaptureRecord:
    id: str
    file_path: str
    captured_at: datetime
    source: str = "camera"


def capture_record_from_path(path: Path, source: str = "camera") -> CaptureRecord:
    return CaptureRecord(
        id=str(uuid4()),
        file_path=str(path),
        captured_at=datetime.now(timezone.utc),
        source=source,
    )
