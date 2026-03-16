from __future__ import annotations

import subprocess
import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class CxFreezeAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "cxfreeze"

    def is_available(self) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "cx_Freeze", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def get_version(self) -> str | None:
        result = subprocess.run(
            [sys.executable, "-m", "cx_Freeze", "--version"],
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
            "console_mode",
            "output_dir",
            "hidden_imports",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is None:
            raise ValueError("entry_script is required for cx_Freeze builds")
        if not build_request.entry_script.exists():
            raise FileNotFoundError(f"Entry script not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        command = [sys.executable, "-m", "cx_Freeze", str(build_request.entry_script)]

        if build_request.executable_name:
            command.extend(["--target-name", build_request.executable_name])

        if build_request.output_dir:
            command.extend(["--target-dir", str(build_request.output_dir)])

        if not build_request.console_mode:
            command.extend(["--base-name", "Win32GUI"])

        if build_request.hidden_imports:
            command.extend(["--includes", ",".join(build_request.hidden_imports)])

        command.extend(build_request.raw_builder_args)
        return command
