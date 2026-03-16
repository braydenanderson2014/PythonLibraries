from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class RustBuilderAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "rust"

    def get_language_family(self) -> str:
        return "rust"

    def is_available(self) -> bool:
        return shutil.which("rustc") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["rustc", "--version"],
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
            "source_files",
            "executable_name",
            "output_dir",
            "optimization",
            "debug_symbols",
            "raw_builder_args",
            "compiler_config",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        source = self._entry_source(build_request)
        if source is None:
            raise ValueError("entry_script or first source_files item is required for Rust builds")
        if not source.exists():
            raise FileNotFoundError(f"Rust source not found: {source}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        source = self._entry_source(build_request)
        assert source is not None

        output_name = build_request.executable_name or source.stem
        if build_request.output_dir:
            output_path = build_request.output_dir / output_name
        else:
            output_path = Path(output_name)

        command = ["rustc", str(source), "-o", str(output_path)]

        optimization = self._setting(build_request, "optimization")
        if optimization:
            opt = str(optimization).replace("-O", "")
            command.extend(["-C", f"opt-level={opt}"])

        debug_symbols = self._bool_setting(build_request, "debug_symbols")
        if debug_symbols:
            command.extend(["-C", "debuginfo=2"])

        command.extend(build_request.raw_builder_args)
        return command

    def _entry_source(self, build_request: BuildRequest) -> Path | None:
        if build_request.entry_script is not None:
            return build_request.entry_script
        if build_request.source_files:
            return build_request.source_files[0]
        return None

    def _setting(self, build_request: BuildRequest, key: str) -> str | bool | None:
        direct = getattr(build_request, key)
        if direct not in (None, "", []):
            return direct
        value = build_request.compiler_config.get(key)
        if value in (None, "", []):
            return None
        return value

    def _bool_setting(self, build_request: BuildRequest, key: str) -> bool:
        direct = bool(getattr(build_request, key))
        if direct:
            return True
        return bool(build_request.compiler_config.get(key, False))
