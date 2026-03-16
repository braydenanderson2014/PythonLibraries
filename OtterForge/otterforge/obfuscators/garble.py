from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class GarbleAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "garble"

    def is_available(self) -> bool:
        return shutil.which("garble") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["garble", "version"],
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

        command = ["garble", "-literals", "build"]

        if request.output_dir:
            default_name = source.stem if source.is_file() else "app"
            command.extend(["-o", str(Path(request.output_dir) / default_name)])

        command.extend(request.raw_tool_args)
        command.append(str(source))
        return command

    def get_language_family(self) -> str:
        return "go"
