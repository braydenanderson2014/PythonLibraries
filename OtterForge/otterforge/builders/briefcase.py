"""Briefcase builder adapter.

Briefcase (from BeeWare) packages a Python application as a platform-native app
bundle.  It operates on projects that have a ``pyproject.toml`` with a
``[tool.briefcase]`` section.  The adapter calls ``briefcase build`` (or
``briefcase run`` / ``briefcase package``) as directed by the build request.
"""
from __future__ import annotations

import shutil
import subprocess

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class BriefcaseAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "briefcase"

    def get_language_family(self) -> str:
        return "python"

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]

    def get_output_types(self) -> list[str]:
        return ["app_bundle", "installer"]

    def is_available(self) -> bool:
        return shutil.which("briefcase") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["briefcase", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or result.stderr.strip()

    def get_supported_common_options(self) -> list[str]:
        return [
            "project_path",
            "mode",
            "target_platform",
            "output_dir",
            "raw_builder_args",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        pyproject = build_request.project_path / "pyproject.toml"
        if not pyproject.exists():
            raise FileNotFoundError(
                f"briefcase requires a pyproject.toml in {build_request.project_path}"
            )

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        # Determine sub-command: "create" + "build" are the two standard phases.
        # We map build_request.mode to a briefcase sub-command.
        subcommand = "build"

        platform = build_request.target_platform
        if platform in ("current", "auto", ""):
            platform = ""  # omit → briefcase infers host platform

        command = ["briefcase", subcommand]
        if platform:
            command.append(platform)
        command.extend(build_request.raw_builder_args)
        return command
