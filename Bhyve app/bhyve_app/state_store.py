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
        self._data: dict[str, Any] = {
            "active_runs": {},
            "history": {},
            "sensor_readings": {},
            "motion_pauses": {},
        }
        self.load()

    @staticmethod
    def key(device_id: str, station: int) -> str:
        return f"{device_id}:{station}"

    def load(self) -> None:
        if not self._path.exists():
            self._data = {
                "active_runs": {},
                "history": {},
                "sensor_readings": {},
                "motion_pauses": {},
            }
            return
        self._data = json.loads(self._path.read_text(encoding="utf-8"))
        self._data.setdefault("active_runs", {})
        self._data.setdefault("history", {})
        self._data.setdefault("sensor_readings", {})
        self._data.setdefault("motion_pauses", {})

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

    # ------------------------------------------------------------------
    # External (non-program) watering tracking
    # ------------------------------------------------------------------

    def get_active_external_watering(self, device_id: str) -> dict[str, Any] | None:
        return self._data.get("active_external_waterings", {}).get(device_id)

    def set_active_external_watering(
        self, device_id: str, station: int, started_at: datetime
    ) -> None:
        self._data.setdefault("active_external_waterings", {})[device_id] = {
            "station": station,
            "started_at": _to_iso(started_at),
        }

    def clear_active_external_watering(self, device_id: str) -> None:
        self._data.get("active_external_waterings", {}).pop(device_id, None)

    # ------------------------------------------------------------------
    # External sensor snapshots
    # ------------------------------------------------------------------

    @staticmethod
    def sensor_key(device_id: str | None, station: int | None) -> str:
        if device_id and station is not None:
            return f"{device_id}:{station}"
        if device_id:
            return f"{device_id}:*"
        return "__global__"

    def set_sensor_reading(
        self,
        *,
        device_id: str | None,
        station: int | None,
        reading: dict[str, Any],
    ) -> None:
        key = self.sensor_key(device_id, station)
        self._data.setdefault("sensor_readings", {})[key] = reading

    def get_sensor_reading(
        self,
        device_id: str,
        station: int,
    ) -> dict[str, Any] | None:
        sensor_readings = self._data.get("sensor_readings", {})
        return (
            sensor_readings.get(self.sensor_key(device_id, station))
            or sensor_readings.get(self.sensor_key(device_id, None))
            or sensor_readings.get(self.sensor_key(None, None))
        )

    # ------------------------------------------------------------------
    # Motion pause tracking
    # ------------------------------------------------------------------

    def get_motion_pause(self, device_id: str, station: int, now: datetime) -> dict[str, Any] | None:
        key = self.key(device_id, station)
        pause = self._data.get("motion_pauses", {}).get(key)
        if not pause:
            return None
        expires_at = _from_iso(pause.get("expires_at"))
        if expires_at is None:
            self._data.get("motion_pauses", {}).pop(key, None)
            return None
        if expires_at <= now:
            self._data.get("motion_pauses", {}).pop(key, None)
            return None
        return pause

    def set_motion_pause(
        self,
        device_id: str,
        station: int,
        *,
        paused_at: datetime,
        expires_at: datetime,
        reason: str = "motion_detected",
    ) -> None:
        key = self.key(device_id, station)
        self._data.setdefault("motion_pauses", {})[key] = {
            "paused_at": _to_iso(paused_at),
            "expires_at": _to_iso(expires_at),
            "reason": reason,
        }

    def clear_motion_pause(self, device_id: str, station: int) -> None:
        key = self.key(device_id, station)
        self._data.get("motion_pauses", {}).pop(key, None)

    # ------------------------------------------------------------------
    # Run history
    # ------------------------------------------------------------------

    @staticmethod
    def _entry_started_at(entry: str | dict[str, Any]) -> str | None:
        if isinstance(entry, str):
            return entry
        return entry.get("started_at")

    def record_run(
        self,
        device_id: str,
        station: int,
        started_at: datetime,
        *,
        source: str,
        rule_name: str | None = None,
    ) -> None:
        key = self.key(device_id, station)
        history = self._data["history"].setdefault(key, [])
        entry: dict[str, Any] = {"started_at": _to_iso(started_at), "source": source}
        if rule_name is not None:
            entry["rule_name"] = rule_name
        history.append(entry)
        self._data["history"][key] = history[-200:]

    def last_run_started_at(self, device_id: str, station: int) -> datetime | None:
        key = self.key(device_id, station)
        history = self._data["history"].get(key, [])
        if not history:
            return None
        return _from_iso(self._entry_started_at(history[-1]))

    def runs_today(self, device_id: str, station: int, now: datetime) -> int:
        key = self.key(device_id, station)
        history = self._data["history"].get(key, [])
        current_date = now.date()
        count = 0
        for entry in history:
            parsed = _from_iso(self._entry_started_at(entry))
            if parsed is None:
                continue
            if parsed.astimezone(now.tzinfo or timezone.utc).date() == current_date:
                count += 1
        return count

    def get_recent_history(self, limit: int = 30) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for key, entries in self._data.get("history", {}).items():
            device_id, _, station_str = key.partition(":")
            for entry in entries:
                if isinstance(entry, str):
                    results.append(
                        {
                            "device_id": device_id,
                            "station": int(station_str),
                            "started_at": entry,
                            "source": "program",
                            "rule_name": None,
                        }
                    )
                else:
                    results.append(
                        {
                            "device_id": device_id,
                            "station": int(station_str),
                            "started_at": entry.get("started_at"),
                            "source": entry.get("source", "program"),
                            "rule_name": entry.get("rule_name"),
                        }
                    )
        results.sort(key=lambda x: x["started_at"] or "", reverse=True)
        return results[:limit]
