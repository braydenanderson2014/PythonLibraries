"""py2exe builder adapter (Windows only).

py2exe creates Windows executables from Python scripts.
It is only meaningful on Windows.  The adapter surfaces as unavailable
on other platforms rather than raising an error at import time.

CLI invocation::

    python setup.py py2exe
"""
from __future__ import annotations

import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest

_IS_WINDOWS = sys.platform == "win32"


class Py2ExeAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "py2exe"

    def get_language_family(self) -> str:
        return "python"

    def get_supported_platforms(self) -> list[str]:
        return ["windows"]

    def get_output_types(self) -> list[str]:
        return ["executable"]

    def is_available(self) -> bool:
        if not _IS_WINDOWS:
            return False
        try:
            import py2exe  # noqa: F401
            return True
        except ImportError:
            return False

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        try:
            import importlib.metadata
            return importlib.metadata.version("py2exe")
        except Exception:
            return None

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "icon_path",
            "output_dir",
            "console_mode",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if not _IS_WINDOWS:
            raise RuntimeError("py2exe is only supported on Windows")
        if build_request.entry_script is None:
            raise ValueError("entry_script is required for py2exe builds")
        if not build_request.entry_script.exists():
            raise FileNotFoundError(f"Entry script not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        setup_py = build_request.project_path / "setup.py"
        if setup_py.exists():
            command = [sys.executable, str(setup_py), "py2exe"]
        else:
            command = [sys.executable, "setup.py", "py2exe"]
        command.extend(build_request.raw_builder_args)
        return command
