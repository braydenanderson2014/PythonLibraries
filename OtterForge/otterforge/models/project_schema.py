from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProjectSchema:
    project: dict[str, Any] = field(default_factory=dict)
    layout: dict[str, Any] = field(default_factory=dict)
    entry_points: list[dict[str, Any]] = field(default_factory=list)
    assets: dict[str, Any] = field(default_factory=dict)
    workflows: list[dict[str, Any]] = field(default_factory=list)