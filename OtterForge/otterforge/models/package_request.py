"""PackageRequest model — input for a packaging operation."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PackageRequest:
    """Describes a single packaging run (wheel, sdist, etc.)."""

    project_path: Path
    packager_name: str = "auto"
    # "wheel", "sdist", "all", or packager-specific format
    package_format: str = "wheel"
    # e.g. {"name": "myapp", "version": "1.0.0", "author": "..."}
    package_metadata: dict[str, str] = field(default_factory=dict)
    output_dir: Path | None = None
    raw_packager_args: list[str] = field(default_factory=list)
    environment_overrides: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    profile_name: str | None = None
    project_schema_path: Path | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PackageRequest":
        def to_path(v: Any) -> Path | None:
            return None if v in (None, "") else Path(v)

        return cls(
            project_path=Path(payload.get("project_path", ".")),
            packager_name=str(payload.get("packager_name", "auto")),
            package_format=str(payload.get("package_format", "wheel")),
            package_metadata=dict(payload.get("package_metadata", {})),
            output_dir=to_path(payload.get("output_dir")),
            raw_packager_args=list(payload.get("raw_packager_args", [])),
            environment_overrides=dict(payload.get("environment_overrides", {})),
            dry_run=bool(payload.get("dry_run", False)),
            profile_name=payload.get("profile_name"),
            project_schema_path=to_path(payload.get("project_schema_path")),
        )
