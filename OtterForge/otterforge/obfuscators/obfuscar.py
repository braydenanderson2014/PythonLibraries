from __future__ import annotations

import shutil
import subprocess

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class ObfuscarAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "obfuscar"

    def _command_name(self) -> str:
        if shutil.which("obfuscar.console") is not None:
            return "obfuscar.console"
        return "obfuscar"

    def is_available(self) -> bool:
        return shutil.which("obfuscar.console") is not None or shutil.which("obfuscar") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            [self._command_name(), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or result.stderr.strip()

    def validate_request(self, request: ObfuscationRequest) -> None:
        source = request.source_path or request.project_path
        if not source.exists():
            raise FileNotFoundError(f"Obfuscation source not found: {source}")
        if source.is_dir() and not request.raw_tool_args:
            raise ValueError(
                "obfuscar expects a config or assembly path by default. "
                "Provide raw_tool_args for advanced directory workflows."
            )

    def build_command(self, request: ObfuscationRequest) -> list[str]:
        self.validate_request(request)
        source = request.source_path or request.project_path

        command = [self._command_name(), str(source)]
        command.extend(request.raw_tool_args)
        return command

    def get_language_family(self) -> str:
        return "dotnet"
