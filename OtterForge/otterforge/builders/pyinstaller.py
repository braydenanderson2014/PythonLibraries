from __future__ import annotations

import shutil
import subprocess

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class PyInstallerAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "pyinstaller"

    def is_available(self) -> bool:
        return shutil.which("pyinstaller") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["pyinstaller", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "executable_name",
            "mode",
            "console_mode",
            "icon_path",
            "splash_path",
            "output_dir",
            "clean",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is None:
            raise ValueError("entry_script is required for PyInstaller builds")
        if not build_request.entry_script.exists():
            raise FileNotFoundError(f"Entry script not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        command = ["pyinstaller"]

        command.append("--onefile" if build_request.mode == "onefile" else "--onedir")
        command.append("--console" if build_request.console_mode else "--noconsole")

        if build_request.executable_name:
            command.extend(["--name", build_request.executable_name])
        if build_request.icon_path:
            command.extend(["--icon", str(build_request.icon_path)])
        if build_request.splash_path:
            command.extend(["--splash", str(build_request.splash_path)])
        if build_request.output_dir:
            command.extend(["--distpath", str(build_request.output_dir)])
        if build_request.clean:
            command.append("--clean")

        for hidden_import in build_request.hidden_imports:
            command.extend(["--hidden-import", hidden_import])

        command.extend(build_request.raw_builder_args)
        command.append(str(build_request.entry_script))
        return command