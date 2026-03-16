from __future__ import annotations

import shutil
import subprocess
import sys

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class NuitkaObfuscatorAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "nuitka"

    def _base_command(self) -> list[str]:
        if shutil.which("nuitka") is not None:
            return ["nuitka"]
        return [sys.executable, "-m", "nuitka"]

    def is_available(self) -> bool:
        if shutil.which("nuitka") is not None:
            return True
        probe = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return probe.returncode == 0

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            [*self._base_command(), "--version"],
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
                "Nuitka expects a Python entry file by default. "
                "Provide raw_tool_args for advanced directory workflows."
            )

    def build_command(self, request: ObfuscationRequest) -> list[str]:
        self.validate_request(request)
        source = request.source_path or request.project_path

        command = [*self._base_command(), "--standalone", "--remove-output"]

        if request.recursive:
            command.append("--follow-imports")
        if request.output_dir:
            command.append(f"--output-dir={request.output_dir}")

        command.extend(request.raw_tool_args)
        command.append(str(source))
        return command
