from __future__ import annotations

import shutil
import subprocess

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class CythonizeAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "cythonize"

    def is_available(self) -> bool:
        return shutil.which("cythonize") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["cythonize", "--version"],
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

    def build_command(self, request: ObfuscationRequest) -> list[str]:
        self.validate_request(request)
        source = request.source_path or request.project_path

        command = ["cythonize", "-3", "-i"]
        if request.output_dir:
            command.extend(["--build-dir", str(request.output_dir)])

        command.extend(request.raw_tool_args)
        command.append(str(source))
        return command
