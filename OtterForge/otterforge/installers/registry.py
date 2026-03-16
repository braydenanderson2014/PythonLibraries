from __future__ import annotations

import sys
from typing import Any

from .base import InstallerAdapter
from .inno_setup import InnoSetupAdapter
from .nsis import NSISAdapter
from .wix import WixAdapter
from .appimage import AppImageAdapter
from .pkgbuild import PkgBuildAdapter


_ADAPTERS: dict[str, InstallerAdapter] = {
    "inno": InnoSetupAdapter(),
    "nsis": NSISAdapter(),
    "wix": WixAdapter(),
    "appimage": AppImageAdapter(),
    "pkgbuild": PkgBuildAdapter(),
}


class InstallerRegistry:
    """Look up and auto-resolve installer adapters."""

    def get(self, name: str) -> InstallerAdapter | None:
        return _ADAPTERS.get(name.lower())

    def list_all(self) -> list[dict[str, Any]]:
        return [a.get_info() for a in _ADAPTERS.values()]

    def resolve_installer(self, prefer: str = "") -> str | None:
        """Auto-select an appropriate installer for the current platform.

        Priority:
          - Windows: inno → nsis → wix
          - Linux:   appimage
          - macOS:   pkgbuild
        Returns the installer name, or None if nothing is available.
        """
        if prefer and prefer in _ADAPTERS:
            return prefer

        platform = sys.platform
        if platform.startswith("win"):
            order = ["inno", "nsis", "wix"]
        elif platform.startswith("linux"):
            order = ["appimage"]
        elif platform == "darwin":
            order = ["pkgbuild"]
        else:
            order = list(_ADAPTERS.keys())

        for name in order:
            adapter = _ADAPTERS[name]
            if adapter.is_available():
                return name
        # Fall back to first in order even if not currently installed (dry-run)
        return order[0] if order else None
