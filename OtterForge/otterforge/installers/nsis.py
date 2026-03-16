from __future__ import annotations

from typing import Any

from ..models.installer_request import InstallerRequest
from .base import InstallerAdapter


class NSISAdapter(InstallerAdapter):
    """NSIS (Nullsoft Scriptable Install System) — Windows only."""

    name = "nsis"
    supported_platforms = ("windows",)
    supported_formats = ("exe",)

    def _primary_tool(self) -> str:
        return "makensis"

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "NSIS — open-source Windows installer builder.",
            "platform": "Windows",
            "output_format": "Executable (.exe)",
            "available": self.is_available(),
        }

    def installer_command(self, request: InstallerRequest) -> list[str]:
        cmd = ["makensis"]
        if request.output_dir:
            cmd += [f"/DOUTDIR={request.output_dir}"]
        if request.application_name:
            cmd += [f"/DAPPNAME={request.application_name}"]
        if request.version:
            cmd += [f"/DAPPVERSION={request.version}"]
        if request.vendor:
            cmd += [f"/DVENDOR={request.vendor}"]
        if request.raw_installer_args:
            cmd.extend(request.raw_installer_args)
        # .nsi script is the last positional argument
        if request.source_artifacts:
            cmd.append(request.source_artifacts[0])
        return cmd

    def validate_request(self, request: InstallerRequest) -> list[str]:
        errors = super().validate_request(request)
        if not request.source_artifacts:
            errors.append("nsis: source_artifacts must contain a .nsi script path")
        elif not request.source_artifacts[0].endswith(".nsi"):
            errors.append("nsis: first source artifact must be a .nsi script file")
        return errors
