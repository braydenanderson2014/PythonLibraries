from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class StateStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, Any] = {"active_runs": {}, "history": {}}
        self.load()

    @staticmethod
    def key(device_id: str, station: int) -> str:
        return f"{device_id}:{station}"

    def load(self) -> None:
        if not self._path.exists():
            self._data = {"active_runs": {}, "history": {}}
            return
        self._data = json.loads(self._path.read_text(encoding="utf-8"))
        self._data.setdefault("active_runs", {})
        self._data.setdefault("history", {})

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get_active_run(self, device_id: str, station: int) -> dict[str, Any] | None:
        key = self.key(device_id, station)
        return self._data["active_runs"].get(key)

    def set_active_run(
        self,
        device_id: str,
        station: int,
        *,
        rule_name: str,
        started_at: datetime,
        requested_minutes: float,
        trigger_temperature: float,
    ) -> None:
        key = self.key(device_id, station)
        self._data["active_runs"][key] = {
            "rule_name": rule_name,
            "started_at": _to_iso(started_at),
            "requested_minutes": requested_minutes,
            "trigger_temperature": trigger_temperature,
        }

    def clear_active_run(self, device_id: str, station: int) -> None:
        key = self.key(device_id, station)
        self._data["active_runs"].pop(key, None)

    def record_run(self, device_id: str, station: int, started_at: datetime) -> None:
        key = self.key(device_id, station)
        history = self._data["history"].setdefault(key, [])
        history.append(_to_iso(started_at))
        self._data["history"][key] = history[-200:]

    def last_run_started_at(self, device_id: str, station: int) -> datetime | None:
        key = self.key(device_id, station)
        history = self._data["history"].get(key, [])
        if not history:
            return None
        return _from_iso(history[-1])

    def runs_today(self, device_id: str, station: int, now: datetime) -> int:
        key = self.key(device_id, station)
        history = self._data["history"].get(key, [])
        current_date = now.date()
        count = 0
        for entry in history:
            parsed = _from_iso(entry)
            if parsed is None:
                continue
            if parsed.astimezone(now.tzinfo or timezone.utc).date() == current_date:
                count += 1
        return count
