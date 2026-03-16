from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from otterforge.models.organization_plan import OrganizationPlan
from otterforge.services.organization_manifest import OrganizationManifestService


class ProjectOrganizer:
    def __init__(self, manifest_dir: Path | str) -> None:
        self.manifest_service = OrganizationManifestService(manifest_dir)

    def create_plan(
        self,
        project_or_group: str | Path,
        scan_result: dict[str, Any],
        mode: str = "copy",
    ) -> dict[str, Any]:
        root = Path(project_or_group).resolve()
        if mode not in {"copy", "move"}:
            raise ValueError("mode must be 'copy' or 'move'")

        actions: list[dict[str, Any]] = []
        for record in scan_result.get("files", []):
            source_path = Path(record["path"]).resolve()
            if not source_path.exists():
                continue

            suggested_folder = record.get("suggested_target_folder", "misc")
            target_path = root / suggested_folder / source_path.name
            if target_path.resolve() == source_path:
                continue

            collision_index = 1
            candidate_path = target_path
            while candidate_path.exists() and candidate_path.resolve() != source_path:
                candidate_path = target_path.with_name(
                    f"{target_path.stem}_{collision_index}{target_path.suffix}"
                )
                collision_index += 1

            actions.append(
                {
                    "source": str(source_path),
                    "target": str(candidate_path),
                    "mode": mode,
                    "role": record.get("role", "other"),
                }
            )

        plan = OrganizationPlan(
            plan_id=str(uuid4()),
            root_path=str(root),
            mode=mode,
            actions=actions,
            created_at=datetime.now(UTC).isoformat(),
        )
        return plan.to_dict()

    def save_plan(self, plan: dict[str, Any], output_path: str | Path) -> Path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            json.dump(plan, handle, indent=2, sort_keys=True)
        return destination

    def load_plan(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def apply_plan(
        self,
        plan: dict[str, Any],
        force: bool = False,
        manifest_path: str | Path | None = None,
    ) -> dict[str, Any]:
        operations: list[dict[str, Any]] = []
        for action in plan.get("actions", []):
            source = Path(action["source"])
            target = Path(action["target"])

            if not source.exists():
                operations.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        "status": "skipped-missing-source",
                    }
                )
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not force:
                operations.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        "status": "skipped-target-exists",
                    }
                )
                continue

            if action.get("mode") == "move":
                if target.exists() and force:
                    if target.is_file():
                        target.unlink()
                shutil.move(str(source), str(target))
            else:
                shutil.copy2(source, target)

            operations.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "mode": action.get("mode", "copy"),
                    "status": "applied",
                }
            )

        written_manifest = self.manifest_service.write_manifest(plan, operations, destination=manifest_path)
        return {
            "plan_id": plan.get("plan_id"),
            "operations": operations,
            "manifest_path": str(written_manifest),
        }

    def rollback(self, manifest_path: str | Path, force: bool = False) -> dict[str, Any]:
        manifest = self.manifest_service.load_manifest(manifest_path)
        operations = list(reversed(manifest.get("operations", [])))
        rollback_operations: list[dict[str, Any]] = []

        for operation in operations:
            if operation.get("status") != "applied":
                rollback_operations.append(
                    {
                        "source": operation.get("source"),
                        "target": operation.get("target"),
                        "status": "skipped-not-applied",
                    }
                )
                continue

            source = Path(operation["source"])
            target = Path(operation["target"])
            mode = operation.get("mode", "copy")

            if mode == "move":
                if not target.exists():
                    rollback_operations.append(
                        {
                            "source": str(source),
                            "target": str(target),
                            "status": "skipped-missing-target",
                        }
                    )
                    continue
                source.parent.mkdir(parents=True, exist_ok=True)
                if source.exists() and not force:
                    rollback_operations.append(
                        {
                            "source": str(source),
                            "target": str(target),
                            "status": "skipped-source-exists",
                        }
                    )
                    continue
                if source.exists() and force and source.is_file():
                    source.unlink()
                shutil.move(str(target), str(source))
                rollback_operations.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        "status": "rolled-back",
                    }
                )
            else:
                if not target.exists():
                    rollback_operations.append(
                        {
                            "source": str(source),
                            "target": str(target),
                            "status": "skipped-missing-target",
                        }
                    )
                    continue
                target.unlink()
                rollback_operations.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        "status": "rolled-back",
                    }
                )

        return {
            "manifest_path": str(manifest_path),
            "operations": rollback_operations,
        }
