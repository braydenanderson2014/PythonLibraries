from __future__ import annotations

import os
from typing import Any

from ..models.installer_request import InstallerRequest
from .base import InstallerAdapter


class AppImageAdapter(InstallerAdapter):
    """AppImage builder — Linux only."""

    name = "appimage"
    supported_platforms = ("linux",)
    supported_formats = ("AppImage",)

    def _primary_tool(self) -> str:
        return "appimagetool"

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "appimagetool — create portable AppImage bundles for Linux.",
            "platform": "Linux",
            "output_format": "AppImage",
            "available": self.is_available(),
        }

    def installer_command(self, request: InstallerRequest) -> list[str]:
        app_dir = request.source_artifacts[0] if request.source_artifacts else "AppDir"
        out_name = (request.application_name or "app").replace(" ", "_") + ".AppImage"
        output_path = os.path.join(request.output_dir, out_name)
        cmd = ["appimagetool"]
        cmd += request.raw_installer_args
        cmd += [app_dir, output_path]
        return cmd

    def validate_request(self, request: InstallerRequest) -> list[str]:
        errors = super().validate_request(request)
        if not request.source_artifacts:
            errors.append("appimage: source_artifacts must contain the path to an AppDir")
        return errors
