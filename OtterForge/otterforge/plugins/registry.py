from __future__ import annotations

from typing import Any


class PluginRegistry:
    """Track loaded OtterForge plugins in memory."""

    def __init__(self) -> None:
        # name -> metadata dict
        self.plugins: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        path: str,
        builders: list = (),
        packagers: list = (),
        installers: list = (),
    ) -> dict[str, Any]:
        entry = {
            "name": name,
            "path": path,
            "builders": [getattr(b, "name", str(b)) for b in builders],
            "packagers": [getattr(p, "name", str(p)) for p in packagers],
            "installers": [getattr(i, "name", str(i)) for i in installers],
        }
        self.plugins[name] = entry
        return entry

    def unregister(self, name: str) -> dict[str, Any]:
        if name not in self.plugins:
            return {"success": False, "error": f"Plugin '{name}' is not registered"}
        entry = self.plugins.pop(name)
        return {"success": True, "removed": entry}

    def list_plugins(self) -> list[dict[str, Any]]:
        return list(self.plugins.values())

    def get(self, name: str) -> dict[str, Any] | None:
        return self.plugins.get(name)
