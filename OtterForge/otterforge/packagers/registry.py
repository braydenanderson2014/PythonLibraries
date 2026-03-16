"""Packager registry — analogous to BuilderRegistry."""
from __future__ import annotations

from otterforge.packagers.base import PackagerAdapter
from otterforge.packagers.build_packager import BuildPackagerAdapter
from otterforge.packagers.hatch_packager import HatchPackagerAdapter
from otterforge.packagers.poetry_packager import PoetryPackagerAdapter
from otterforge.packagers.setuptools_packager import SetuptoolsPackagerAdapter


class PackagerRegistry:
    def __init__(self) -> None:
        self._packagers: dict[str, PackagerAdapter] = {}
        self.register(BuildPackagerAdapter())
        self.register(SetuptoolsPackagerAdapter())
        self.register(HatchPackagerAdapter())
        self.register(PoetryPackagerAdapter())

    def register(self, adapter: PackagerAdapter) -> None:
        self._packagers[adapter.name] = adapter

    def get(self, name: str) -> PackagerAdapter:
        if name not in self._packagers:
            raise KeyError(f"Unknown packager: {name}")
        return self._packagers[name]

    def list_packagers(self) -> list[dict[str, object]]:
        return [
            {
                "name": adapter.name,
                "available": adapter.is_available(),
                "version": adapter.get_version(),
                "formats": adapter.get_supported_formats(),
                "platforms": adapter.get_supported_platforms(),
            }
            for adapter in self._packagers.values()
        ]

    def inspect(self, name: str) -> dict[str, object]:
        adapter = self.get(name)
        return {
            "name": adapter.name,
            "available": adapter.is_available(),
            "version": adapter.get_version(),
            "formats": adapter.get_supported_formats(),
            "platforms": adapter.get_supported_platforms(),
        }

    def resolve_packager(self, request_packager: str, project_path: object) -> str:
        """Resolve 'auto' to the best available packager for the project."""
        if request_packager not in ("auto", ""):
            return request_packager

        from pathlib import Path
        path = Path(str(project_path))

        # Prefer: hatch > poetry > build > setuptools (based on project signals)
        if (path / "pyproject.toml").exists():
            content = (path / "pyproject.toml").read_text(errors="replace")
            if "tool.hatch" in content and self._packagers["hatch"].is_available():
                return "hatch"
            if "tool.poetry" in content and self._packagers["poetry"].is_available():
                return "poetry"
            return "build"
        if (path / "setup.py").exists() and self._packagers["setuptools"].is_available():
            return "setuptools"
        if self._packagers["build"].is_available():
            return "build"
        return "setuptools"
