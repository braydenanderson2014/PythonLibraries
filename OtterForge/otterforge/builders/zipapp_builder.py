"""zipapp builder adapter.

Python's stdlib ``zipapp`` module creates a self-contained ``.pyz`` archive
that can be executed with ``python myapp.pyz``.  No third-party packager is
required — ``zipapp`` is part of the standard library since Python 3.5.

CLI invocation::

    python -m zipapp myapp/ -m "myapp.__main__:main" -o dist/myapp.pyz
"""
from __future__ import annotations

import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class ZipAppAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "zipapp"

    def get_language_family(self) -> str:
        return "python"

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]

    def get_output_types(self) -> list[str]:
        return ["pyz"]

    def is_available(self) -> bool:
        # zipapp is part of the standard library; always available
        try:
            import zipapp  # noqa: F401
            return True
        except ImportError:
            return False

    def get_version(self) -> str | None:
        # No separate version — report the Python version
        return f"stdlib (Python {sys.version.split()[0]})"

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "output_dir",
            "project_path",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is None:
            raise ValueError(
                "zipapp requires an entry_script (module:callable) via --entry"
            )

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)

        output_dir = build_request.output_dir or (build_request.project_path / "dist")
        name = build_request.executable_name or "app"
        output_file = output_dir / f"{name}.pyz"

        command = [sys.executable, "-m", "zipapp"]

        # Source directory or file to package
        command.append(str(build_request.project_path))

        # entry point as module:callable
        entry = str(build_request.entry_script)
        command.extend(["-m", entry])

        command.extend(["-o", str(output_file)])
        command.extend(build_request.raw_builder_args)
        return command
