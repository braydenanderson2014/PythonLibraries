from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class InstallerResult:
    """Result returned by every InstallerAdapter run."""

    success: bool = False
    exit_code: int = -1
    final_command: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    installer_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "final_command": self.final_command,
            "artifact_paths": self.artifact_paths,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "installer_name": self.installer_name,
        }

    @classmethod
    def failure(cls, reason: str, installer_name: str = "") -> "InstallerResult":
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            success=False,
            exit_code=-1,
            stderr=reason,
            started_at=now,
            finished_at=now,
            duration_seconds=0.0,
            installer_name=installer_name,
        )
