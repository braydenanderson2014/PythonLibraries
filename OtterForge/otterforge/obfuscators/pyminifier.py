from __future__ import annotations

import shutil
import subprocess

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.obfuscators.base import ObfuscatorAdapter


class PyMinifierAdapter(ObfuscatorAdapter):
    @property
    def name(self) -> str:
        return "pyminifier"

    def is_available(self) -> bool:
        return shutil.which("pyminifier") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["pyminifier", "--version"],
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
                "pyminifier primarily targets single Python files. "
                "Pass custom recursive flags via raw_tool_args if needed."
            )

    def build_command(self, request: ObfuscationRequest) -> list[str]:
        self.validate_request(request)
        source = request.source_path or request.project_path

        command = ["pyminifier", "--obfuscate"]

        if request.output_dir and source.is_file():
            has_outfile_arg = any(
                item in {"-o", "--outfile"}
                or item.startswith("-o=")
                or item.startswith("--outfile=")
                for item in request.raw_tool_args
            )
            if not has_outfile_arg:
                command.extend(["-o", str(request.output_dir / source.name)])

        command.extend(request.raw_tool_args)
        command.append(str(source))
        return command
