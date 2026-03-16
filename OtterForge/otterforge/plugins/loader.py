from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from .registry import PluginRegistry


class PluginLoader:
    """Discover and load OtterForge plugin modules from a directory.

    A plugin module may expose:
    - BUILDER_ADAPTERS: list of BuilderAdapter subclass instances to register
    - PACKAGER_ADAPTERS: list of PackagerAdapter subclass instances to register
    - INSTALLER_ADAPTERS: list of InstallerAdapter subclass instances to register
    """

    def __init__(self, plugin_dir: str | Path | None = None) -> None:
        self.plugin_dir = Path(plugin_dir) if plugin_dir else self._default_plugin_dir()
        self.registry = PluginRegistry()

    @staticmethod
    def _default_plugin_dir() -> Path:
        data_home = Path(os.environ.get("OTTERFORGE_DATA_DIR", Path.home() / ".otterforge"))
        return data_home / "plugins"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self) -> list[dict[str, Any]]:
        """Scan plugin_dir for .py files and return metadata without loading."""
        if not self.plugin_dir.is_dir():
            return []
        results = []
        for path in sorted(self.plugin_dir.glob("*.py")):
            results.append({"name": path.stem, "path": str(path), "loaded": path.stem in self.registry.plugins})
        return results

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, name: str) -> dict[str, Any]:
        """Load a plugin by stem name from plugin_dir."""
        path = self.plugin_dir / f"{name}.py"
        if not path.exists():
            return {"success": False, "error": f"Plugin file not found: {path}"}
        return self._load_path(path)

    def load_path(self, file_path: str | Path) -> dict[str, Any]:
        """Load a plugin from an explicit file path."""
        return self._load_path(Path(file_path))

    def _load_path(self, path: Path) -> dict[str, Any]:
        name = path.stem
        spec = importlib.util.spec_from_file_location(f"otterforge_plugin_{name}", path)
        if spec is None or spec.loader is None:
            return {"success": False, "error": f"Cannot create module spec for {path}"}

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        builders = getattr(module, "BUILDER_ADAPTERS", [])
        packagers = getattr(module, "PACKAGER_ADAPTERS", [])
        installers = getattr(module, "INSTALLER_ADAPTERS", [])

        self.registry.register(name, str(path), builders=builders, packagers=packagers, installers=installers)
        return {
            "success": True,
            "name": name,
            "path": str(path),
            "builders": [getattr(b, "name", str(b)) for b in builders],
            "packagers": [getattr(p, "name", str(p)) for p in packagers],
            "installers": [getattr(i, "name", str(i)) for i in installers],
        }

    # ------------------------------------------------------------------
    # Unloading
    # ------------------------------------------------------------------

    def unload(self, name: str) -> dict[str, Any]:
        return self.registry.unregister(name)

    # ------------------------------------------------------------------
    # Install (copy a plugin file into plugin_dir)
    # ------------------------------------------------------------------

    def install(self, source_path: str | Path) -> dict[str, Any]:
        """Copy a plugin file into plugin_dir and load it."""
        import shutil
        src = Path(source_path)
        if not src.exists():
            return {"success": False, "error": f"Source file not found: {src}"}
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        dest = self.plugin_dir / src.name
        shutil.copy2(src, dest)
        return self._load_path(dest)
