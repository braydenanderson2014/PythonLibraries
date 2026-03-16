from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .memory_store import DEFAULT_MEMORY_STATE, MemoryStore, create_default_memory_state


class SQLMemoryStore(MemoryStore):
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(str(self.database_path))
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    @property
    def backend_name(self) -> str:
        return "sql"

    def _initialize_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_sections (
                section TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def load_state(self) -> dict[str, Any]:
        state = create_default_memory_state()
        rows = self._connection.execute(
            "SELECT section, payload FROM memory_sections"
        ).fetchall()
        for row in rows:
            if row["section"] in state:
                state[row["section"]] = json.loads(row["payload"])
        return state

    def save_state(self, state: dict[str, Any]) -> None:
        merged = create_default_memory_state()
        merged.update(state)
        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            for section, payload in merged.items():
                self._connection.execute(
                    """
                    INSERT INTO memory_sections(section, payload, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(section) DO UPDATE SET
                        payload = excluded.payload,
                        updated_at = excluded.updated_at
                    """,
                    (section, json.dumps(payload, sort_keys=True), timestamp),
                )

    def close(self) -> None:
        self._connection.close()