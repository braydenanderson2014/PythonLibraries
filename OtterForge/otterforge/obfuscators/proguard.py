from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class ProGuardAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "proguard"

    def is_available(self) -> bool:
        return shutil.which("proguard") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["proguard", "-version"],
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
                "proguard expects an input jar by default. "
                "Provide raw_tool_args for advanced directory/config workflows."
            )

    def build_command(self, request: ObfuscationRequest) -> list[str]:
        self.validate_request(request)
        source = request.source_path or request.project_path

        command = ["proguard", "-injars", str(source)]

        if request.output_dir:
            if source.is_file():
                output_name = f"{source.stem}-obf{source.suffix or '.jar'}"
            else:
                output_name = "obfuscated.jar"
            command.extend(["-outjars", str(Path(request.output_dir) / output_name)])

        command.extend(request.raw_tool_args)
        return command

    def get_language_family(self) -> str:
        return "java"
