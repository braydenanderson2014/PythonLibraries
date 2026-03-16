"""py2app builder adapter (macOS only).

py2app creates native macOS ``.app`` bundles from Python scripts.
It is only meaningful on macOS.  The adapter surfaces as unavailable
on other platforms rather than raising an error at import time.

CLI invocation::

    python setup.py py2app
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest

_IS_MACOS = sys.platform == "darwin"


class Py2AppAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "py2app"

    def get_language_family(self) -> str:
        return "python"

    def get_supported_platforms(self) -> list[str]:
        return ["macos"]

    def get_output_types(self) -> list[str]:
        return ["app_bundle"]

    def is_available(self) -> bool:
        if not _IS_MACOS:
            return False
        # py2app is a setuptools command; check for the package
        try:
            import py2app  # noqa: F401
            return True
        except ImportError:
            return False

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        try:
            import importlib.metadata
            return importlib.metadata.version("py2app")
        except Exception:
            return None

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "icon_path",
            "output_dir",
            "mode",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if not _IS_MACOS:
            raise RuntimeError("py2app is only supported on macOS")
        if build_request.entry_script is None:
            raise ValueError("entry_script is required for py2app builds")
        if not build_request.entry_script.exists():
            raise FileNotFoundError(f"Entry script not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        command = [sys.executable, str(build_request.entry_script)]
        # py2app operates via a setup.py-style invocation; in modern usage
        # the user typically has a setup.py or pyproject with py2app config.
        # We emit the canonical "python setup.py py2app" invocation.
        setup_py = build_request.project_path / "setup.py"
        if setup_py.exists():
            command = [sys.executable, str(setup_py), "py2app"]
        else:
            command = [sys.executable, "setup.py", "py2app"]

        if build_request.mode == "onefile":
            command.append("--semi-standalone")

        command.extend(build_request.raw_builder_args)
        return command
