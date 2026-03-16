from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class OrganizationManifestService:
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_manifest(
        self,
        plan: dict[str, Any],
        operations: list[dict[str, Any]],
        destination: str | Path | None = None,
    ) -> Path:
        payload = {
            "manifest_id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "plan": plan,
            "operations": operations,
        }

        output_path = Path(destination) if destination else self.base_dir / f"manifest_{payload['manifest_id']}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return output_path

    def load_manifest(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
