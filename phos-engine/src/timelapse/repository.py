from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from src.timelapse.domain import TimelapsePlan


class JsonTimelapsePlanRepository:
    def __init__(self, storage_file: Path) -> None:
        self._storage_file = storage_file
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)

    def save(self, plan: TimelapsePlan) -> TimelapsePlan:
        plans = {item.id: item for item in self.list_all()}
        plans[plan.id] = plan
        payload = [self._serialize(item) for item in plans.values()]
        self._storage_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return plan

    def get(self, plan_id: str) -> TimelapsePlan | None:
        for plan in self.list_all():
            if plan.id == plan_id:
                return plan
        return None

    def list_all(self) -> list[TimelapsePlan]:
        if not self._storage_file.exists():
            return []
        try:
            payload = json.loads(self._storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        plans: list[TimelapsePlan] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            plans.append(self._deserialize(item))
        return plans

    @staticmethod
    def _serialize(plan: TimelapsePlan) -> dict[str, str | int | bool | None]:
        return {
            "id": plan.id,
            "interval_seconds": plan.interval_seconds,
            "window_start_hour": plan.window_start_hour,
            "window_end_hour": plan.window_end_hour,
            "active": plan.active,
            "last_capture_at": plan.last_capture_at.isoformat() if plan.last_capture_at else None,
        }

    @staticmethod
    def _deserialize(item: dict[str, str | int | bool | None]) -> TimelapsePlan:
        last_capture = item.get("last_capture_at")
        last_capture_at = None
        if isinstance(last_capture, str):
            last_capture_at = datetime.fromisoformat(last_capture).astimezone(timezone.utc)
        return TimelapsePlan(
            id=str(item["id"]),
            interval_seconds=int(item["interval_seconds"]),
            window_start_hour=int(item["window_start_hour"]),
            window_end_hour=int(item["window_end_hour"]),
            active=bool(item.get("active", False)),
            last_capture_at=last_capture_at,
        )
