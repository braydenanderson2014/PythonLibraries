from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .memory_store import DEFAULT_MEMORY_STATE, MemoryStore, create_default_memory_state


JSON_SECTION_FILES = {
    "user_settings": "user_settings.json",
    "projects": "projects.json",
    "build_history": "build_history.json",
    "profiles": "profiles.json",
    "hooks": "hooks.json",
    "test_configs": "test_configs.json",
    "signing_configs": "signing_configs.json",
    "audit_configs": "audit_configs.json",
    "notification_settings": "notification_settings.json",
    "container_configs": "container_configs.json",
    "matrix_configs": "matrix_configs.json",
}


class JsonMemoryStore(MemoryStore):
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(str(self.data_dir))

    @property
    def backend_name(self) -> str:
        return "json"

    def load_state(self) -> dict[str, Any]:
        state = create_default_memory_state()
        for section, file_name in JSON_SECTION_FILES.items():
            file_path = self.data_dir / file_name
            if not file_path.exists():
                continue
            with file_path.open("r", encoding="utf-8") as handle:
                state[section] = json.load(handle)
        return state

    def save_state(self, state: dict[str, Any]) -> None:
        merged = create_default_memory_state()
        merged.update(state)
        for section in DEFAULT_MEMORY_STATE:
            file_path = self.data_dir / JSON_SECTION_FILES[section]
            with file_path.open("w", encoding="utf-8") as handle:
                json.dump(merged[section], handle, indent=2, sort_keys=True)