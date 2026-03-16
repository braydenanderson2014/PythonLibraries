from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from otterforge.services.memory_migrator import MemoryMigrator
from otterforge.storage.json_store import JsonMemoryStore
from otterforge.storage.memory_store import MemoryStore
from otterforge.storage.sql_store import SQLMemoryStore
from otterforge.utils.paths import resolve_data_dir, resolve_runtime_config_path, resolve_sqlite_path


DEFAULT_RUNTIME_CONFIG: dict[str, Any] = {
    "memory_backend": "json",
    "mcp": {
        "enabled": False,
        "transport": "stdio",
        "read_only": True,
        "exposed_tools": [
            "scan_project",
            "list_builders",
            "inspect_builder",
            "list_obfuscators",
            "inspect_obfuscator",
            "list_modules",
            "doctor_toolchain",
            "list_language_packs",
            "show_manifest",
            "list_compiler_configs",
            "show_compiler_config",
            "list_profiles",
            "show_profile",
            "create_organization_plan",
            "list_artifacts",
            "get_build_history",
            "load_memory",
            "get_memory_backend",
            "get_mcp_status",
            "list_mcp_tools",
        ],
    },
}


class MemoryBackendManager:
    def __init__(self, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root).resolve() if project_root else None
        self.data_dir = resolve_data_dir(self.project_root)
        self.runtime_config_path = resolve_runtime_config_path(self.project_root)
        self.sqlite_path = resolve_sqlite_path(self.project_root)

    def load_runtime_config(self) -> dict[str, Any]:
        if not self.runtime_config_path.exists():
            config = self._build_default_config()
            self.save_runtime_config(config)
            return config

        with self.runtime_config_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)

        config = self._build_default_config()
        config.update({key: value for key, value in loaded.items() if key != "mcp"})
        config["mcp"].update(loaded.get("mcp", {}))
        return config

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.runtime_config_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, sort_keys=True)

    def _build_default_config(self) -> dict[str, Any]:
        config = json.loads(json.dumps(DEFAULT_RUNTIME_CONFIG))
        config["json_data_dir"] = str(self.data_dir)
        config["sql_database_path"] = str(self.sqlite_path)
        return config

    def get_backend_name(self) -> str:
        return str(self.load_runtime_config().get("memory_backend", "json"))

    def get_store(self, backend: str | None = None) -> MemoryStore:
        selected = backend or self.get_backend_name()
        config = self.load_runtime_config()

        if selected == "json":
            return JsonMemoryStore(config["json_data_dir"])
        if selected == "sql":
            return SQLMemoryStore(config["sql_database_path"])
        raise ValueError(f"Unsupported memory backend: {selected}")

    def get_status(self) -> dict[str, Any]:
        config = self.load_runtime_config()
        return {
            "backend": config["memory_backend"],
            "json_data_dir": config["json_data_dir"],
            "sql_database_path": config["sql_database_path"],
            "runtime_config_path": str(self.runtime_config_path),
        }

    def set_backend(self, backend: str, config_update: dict[str, Any] | None = None) -> dict[str, Any]:
        if backend not in {"json", "sql"}:
            raise ValueError("backend must be 'json' or 'sql'")

        config = self.load_runtime_config()
        config["memory_backend"] = backend
        if config_update:
            config.update(config_update)
        self.save_runtime_config(config)
        return self.get_status()

    def migrate_to(self, target_backend: str) -> dict[str, Any]:
        current_backend = self.get_backend_name()
        if current_backend == target_backend:
            return {
                "source_backend": current_backend,
                "target_backend": target_backend,
                "migrated": False,
                "reason": "already-using-target-backend",
            }

        source_store = self.get_store(current_backend)
        target_store = self.get_store(target_backend)
        try:
            summary = MemoryMigrator.migrate(source_store, target_store)
        finally:
            source_store.close()
            target_store.close()

        self.set_backend(target_backend)
        summary["migrated"] = True
        return summary

    def read_memory(self) -> dict[str, Any]:
        store = self.get_store()
        try:
            return store.load_state()
        finally:
            store.close()

    def write_user_setting(self, key: str, value: Any) -> dict[str, Any]:
        store = self.get_store()
        try:
            state = store.load_state()
            state["user_settings"][key] = value
            store.save_state(state)
            return state["user_settings"]
        finally:
            store.close()

    def get_user_setting(self, key: str) -> Any:
        return self.read_memory()["user_settings"].get(key)

    def clear_memory(self, scope: str, project_name: str | None = None) -> dict[str, Any]:
        store = self.get_store()
        try:
            return store.clear(scope, project_name=project_name)
        finally:
            store.close()