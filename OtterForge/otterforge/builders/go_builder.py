from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class GoBuilderAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "go"

    def get_language_family(self) -> str:
        return "go"

    def is_available(self) -> bool:
        return shutil.which("go") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["go", "version"],
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
            "optimization",
            "debug_symbols",
            "raw_builder_args",
            "compiler_config",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        if build_request.entry_script is not None and not build_request.entry_script.exists():
            raise FileNotFoundError(f"Go target path not found: {build_request.entry_script}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)

        target = str(build_request.entry_script) if build_request.entry_script is not None else "."
        output_name = build_request.executable_name or "app"
        if build_request.output_dir:
            output_path = build_request.output_dir / output_name
        else:
            output_path = Path(output_name)

        command = ["go", "build", "-o", str(output_path)]

        debug_symbols = self._bool_setting(build_request, "debug_symbols")
        if debug_symbols:
            command.extend(["-gcflags", "all=-N -l"])

        command.extend(build_request.raw_builder_args)
        command.append(target)
        return command

    def _bool_setting(self, build_request: BuildRequest, key: str) -> bool:
        direct = bool(getattr(build_request, key))
        if direct:
            return True
        return bool(build_request.compiler_config.get(key, False))
