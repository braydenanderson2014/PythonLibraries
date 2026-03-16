from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class OrganizationPlan:
    plan_id: str
    root_path: str
    mode: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "root_path": self.root_path,
            "mode": self.mode,
            "actions": self.actions,
            "created_at": self.created_at,
        }
