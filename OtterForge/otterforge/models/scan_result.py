from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ScanResult:
    path: str
    scope: str
    entry_points: list[str] = field(default_factory=list)
    spec_files: list[str] = field(default_factory=list)
    files: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "scope": self.scope,
            "entry_points": self.entry_points,
            "spec_files": self.spec_files,
            "files": self.files,
        }
