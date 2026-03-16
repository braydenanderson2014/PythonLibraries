"""PyPA build packager adapter.

Uses ``python -m build`` (PyPA build frontend) to create wheels and sdists.
Requires the ``build`` package: ``pip install build``.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys

from otterforge.models.package_request import PackageRequest
from otterforge.packagers.base import PackagerAdapter


class BuildPackagerAdapter(PackagerAdapter):
    @property
    def name(self) -> str:
        return "build"

    def get_supported_formats(self) -> list[str]:
        return ["wheel", "sdist", "all"]

    def is_available(self) -> bool:
        return importlib.util.find_spec("build") is not None or shutil.which("pyproject-build") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        try:
            import importlib.metadata
            return importlib.metadata.version("build")
        except Exception:
            return None

    def package_command(self, request: PackageRequest) -> list[str]:
        command = [sys.executable, "-m", "build"]

        fmt = request.package_format.lower()
        if fmt == "wheel":
            command.append("--wheel")
        elif fmt == "sdist":
            command.append("--sdist")
        # "all" → omit format flag (build produces both by default)

        if request.output_dir:
            command.extend(["--outdir", str(request.output_dir)])

        command.extend(request.raw_packager_args)
        command.append(str(request.project_path))
        return command
