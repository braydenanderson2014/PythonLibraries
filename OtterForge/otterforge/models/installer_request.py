from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InstallerRequest:
    """Normalised request passed to every InstallerAdapter."""

    # Required
    project_path: str = ""

    # Adapter selection
    installer_name: str = ""          # e.g. "inno", "nsis", "wix", "appimage", "pkgbuild"

    # Source artefacts to package into the installer
    source_artifacts: list[str] = field(default_factory=list)

    # Installer metadata
    installer_format: str = ""        # e.g. "exe", "msi", "pkg", "AppImage"
    application_name: str = ""
    version: str = ""
    vendor: str = ""
    install_root: str = ""            # Default install directory on target OS
    shortcuts: list[dict[str, str]] = field(default_factory=list)  # [{name, target}]
    license_file: str = ""

    # Output
    output_dir: str = "dist"

    # Pass-through
    raw_installer_args: list[str] = field(default_factory=list)
    environment_overrides: dict[str, str] = field(default_factory=dict)

    # Execution flags
    dry_run: bool = False

    # Optional project schema / profile
    profile_name: str = ""
    project_schema_path: str = ""

    def __post_init__(self) -> None:
        if self.project_path:
            self.project_path = os.path.abspath(self.project_path)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstallerRequest":
        obj = cls()
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        if obj.project_path:
            obj.project_path = os.path.abspath(obj.project_path)
        return obj
