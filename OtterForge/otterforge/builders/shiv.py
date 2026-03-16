"""shiv builder adapter.

shiv creates a zipapp-style single-file executable (a ``.pyz`` file with an
embedded virtual environment).  The resulting file requires Python to be
installed on the target machine.

CLI invocation pattern::

    shiv -o dist/myapp.pyz -e myapp.__main__:main .
"""
from __future__ import annotations

import subprocess
import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class ShivAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "shiv"

    def get_language_family(self) -> str:
        return "python"

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]

    def get_output_types(self) -> list[str]:
        return ["pyz"]

    def is_available(self) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "shiv", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def get_version(self) -> str | None:
        result = subprocess.run(
            [sys.executable, "-m", "shiv", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or result.stderr.strip()

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "output_dir",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is None:
            raise ValueError(
                "shiv requires an entry_script (module:callable) via --entry"
            )

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)

        output_dir = build_request.output_dir or (build_request.project_path / "dist")
        name = build_request.executable_name or "app"
        output_file = output_dir / f"{name}.pyz"

        command = [sys.executable, "-m", "shiv", "-o", str(output_file)]

        # entry_script stores the module:callable string for --entry or -e
        entry = str(build_request.entry_script)
        command.extend(["-e", entry])

        command.extend(build_request.raw_builder_args)

        # shiv accepts a source directory or package name at the end
        command.append(str(build_request.project_path))
        return command
