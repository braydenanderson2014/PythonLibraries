"""Setuptools packager adapter.

Uses ``python setup.py bdist_wheel`` / ``python setup.py sdist`` to produce
distribution packages.  Modern projects prefer the ``build`` frontend, but
this adapter handles legacy projects that still rely on ``setup.py``.
"""
from __future__ import annotations

import importlib.util
import sys

from otterforge.models.package_request import PackageRequest
from otterforge.packagers.base import PackagerAdapter


class SetuptoolsPackagerAdapter(PackagerAdapter):
    @property
    def name(self) -> str:
        return "setuptools"

    def get_supported_formats(self) -> list[str]:
        return ["wheel", "sdist", "all"]

    def is_available(self) -> bool:
        return importlib.util.find_spec("setuptools") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        try:
            import importlib.metadata
            return importlib.metadata.version("setuptools")
        except Exception:
            return None

    def validate_request(self, request: PackageRequest) -> None:
        setup_py = request.project_path / "setup.py"
        if not setup_py.exists():
            raise FileNotFoundError(
                f"setuptools adapter requires setup.py in {request.project_path}"
            )

    def package_command(self, request: PackageRequest) -> list[str]:
        self.validate_request(request)
        setup_py = request.project_path / "setup.py"
        fmt = request.package_format.lower()

        if fmt == "wheel":
            subcmds = ["bdist_wheel"]
        elif fmt == "sdist":
            subcmds = ["sdist"]
        else:  # "all"
            subcmds = ["sdist", "bdist_wheel"]

        command = [sys.executable, str(setup_py)] + subcmds
        if request.output_dir:
            command.extend(["--dist-dir", str(request.output_dir)])
        command.extend(request.raw_packager_args)
        return command
