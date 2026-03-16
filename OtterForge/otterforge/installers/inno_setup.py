from __future__ import annotations

from typing import Any

from ..models.installer_request import InstallerRequest
from .base import InstallerAdapter


class InnoSetupAdapter(InstallerAdapter):
    """Inno Setup installer creator — Windows only."""

    name = "inno"
    supported_platforms = ("windows",)
    supported_formats = ("exe",)

    def _primary_tool(self) -> str:
        return "iscc"

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "Inno Setup — free scriptable Windows installer builder.",
            "platform": "Windows",
            "output_format": "Executable (.exe)",
            "available": self.is_available(),
        }

    def installer_command(self, request: InstallerRequest) -> list[str]:
        cmd = ["iscc"]
        if request.output_dir:
            cmd += [f"/O{request.output_dir}"]
        if request.application_name:
            cmd += [f"/DMyAppName={request.application_name}"]
        if request.version:
            cmd += [f"/DMyAppVersion={request.version}"]
        if request.vendor:
            cmd += [f"/DMyAppPublisher={request.vendor}"]
        if request.install_root:
            cmd += [f"/DMyAppDefaultDir={request.install_root}"]
        if request.raw_installer_args:
            cmd.extend(request.raw_installer_args)
        # The last positional arg is the .iss script (first source artifact, if any)
        if request.source_artifacts:
            cmd.append(request.source_artifacts[0])
        return cmd

    def validate_request(self, request: InstallerRequest) -> list[str]:
        errors = super().validate_request(request)
        # Inno setup needs a .iss script as input
        if not request.source_artifacts:
            errors.append("inno: source_artifacts must contain the path to a .iss script")
        elif not request.source_artifacts[0].endswith(".iss"):
            errors.append("inno: first source artifact must be a .iss script file")
        return errors
