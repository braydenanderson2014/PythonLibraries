from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ObfuscationResult:
    success: bool
    exit_code: int
    final_command: list[str]
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    tool_name: str = ""
    output_path: str | None = None
    environment_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
