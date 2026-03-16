from __future__ import annotations

from typing import Any

from otterforge.storage.memory_store import MemoryStore


class MemoryMigrator:
    @staticmethod
    def migrate(source: MemoryStore, target: MemoryStore) -> dict[str, Any]:
        state = source.load_state()
        target.save_state(state)
        return {
            "source_backend": source.backend_name,
            "target_backend": target.backend_name,
            "sections": list(state.keys()),
        }