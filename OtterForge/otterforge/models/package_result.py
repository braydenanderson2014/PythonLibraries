"""PackageResult model — output of a packaging operation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PackageResult:
    success: bool
    exit_code: int
    final_command: list[str]
    artifact_paths: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    packager_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
