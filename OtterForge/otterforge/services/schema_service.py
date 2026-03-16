from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaService:
    def export_starter_schema(self, scan_result: dict[str, Any]) -> dict[str, Any]:
        files = scan_result.get("files", [])
        icons = [item["path"] for item in files if item["role"] in {"icon", "icon-candidate"}]
        splash = [item["path"] for item in files if item["role"] in {"splash", "splash-candidate"}]
        docs = [item["path"] for item in files if item["role"] == "documentation"]

        return {
            "project": {"root": scan_result.get("path")},
            "layout": {"scope": scan_result.get("scope", "projects")},
            "entry_points": [{"path": path} for path in scan_result.get("entry_points", [])],
            "assets": {"icons": icons, "splash": splash},
            "documentation": {"files": docs},
            "scan_catalog": files,
        }

    def save_schema(self, schema: dict[str, Any], destination: str | Path) -> Path:
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with destination_path.open("w", encoding="utf-8") as handle:
            json.dump(schema, handle, indent=2, sort_keys=True)
        return destination_path

    def load_schema(self, schema_path: str | Path) -> dict[str, Any]:
        with Path(schema_path).open("r", encoding="utf-8") as handle:
            return json.load(handle)