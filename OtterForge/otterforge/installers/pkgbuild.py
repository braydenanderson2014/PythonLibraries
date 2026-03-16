from __future__ import annotations

import os
from typing import Any

from ..models.installer_request import InstallerRequest
from .base import InstallerAdapter


class PkgBuildAdapter(InstallerAdapter):
    """pkgbuild / productbuild — macOS .pkg installer builder."""

    name = "pkgbuild"
    supported_platforms = ("darwin",)
    supported_formats = ("pkg",)

    def _primary_tool(self) -> str:
        return "pkgbuild"

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "pkgbuild / productbuild — create macOS .pkg installers.",
            "platform": "macOS",
            "output_format": ".pkg installer",
            "available": self.is_available(),
        }

    def installer_command(self, request: InstallerRequest) -> list[str]:
        app_root = request.source_artifacts[0] if request.source_artifacts else request.project_path
        out_name = (request.application_name or "app").replace(" ", "_") + ".pkg"
        output_path = os.path.join(request.output_dir, out_name)

        cmd = ["pkgbuild"]
        if request.install_root:
            cmd += ["--install-location", request.install_root]
        if request.application_name:
            cmd += ["--identifier", f"com.{(request.vendor or 'otterforge').lower()}.{request.application_name.lower().replace(' ', '')}"]
        if request.version:
            cmd += ["--version", request.version]
        cmd += ["--root", app_root]
        cmd += request.raw_installer_args
        cmd.append(output_path)
        return cmd

    def validate_request(self, request: InstallerRequest) -> list[str]:
        errors = super().validate_request(request)
        if not request.source_artifacts and not request.project_path:
            errors.append("pkgbuild: either source_artifacts or project_path must be set")
        return errors
