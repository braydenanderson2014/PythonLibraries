from __future__ import annotations

import subprocess
import sys

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class NuitkaAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "nuitka"

    def is_available(self) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def get_version(self) -> str | None:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip() or result.stderr.strip()
        return output.splitlines()[0] if output else None

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "mode",
            "console_mode",
            "icon_path",
            "output_dir",
            "clean",
            "hidden_imports",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is None:
            raise ValueError("entry_script is required for Nuitka builds")
        if not build_request.entry_script.exists():
            raise FileNotFoundError(f"Entry script not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        command = [sys.executable, "-m", "nuitka", "--standalone"]

        if build_request.mode == "onefile":
            command.append("--onefile")

        if not build_request.console_mode:
            command.append("--disable-console")

        if build_request.executable_name:
            command.append(f"--output-filename={build_request.executable_name}")

        if build_request.output_dir:
            command.append(f"--output-dir={build_request.output_dir}")

        if build_request.icon_path:
            command.append(f"--windows-icon-from-ico={build_request.icon_path}")

        if build_request.clean:
            command.append("--remove-output")

        for hidden_import in build_request.hidden_imports:
            command.append(f"--include-module={hidden_import}")

        command.extend(build_request.raw_builder_args)
        command.append(str(build_request.entry_script))
        return command
