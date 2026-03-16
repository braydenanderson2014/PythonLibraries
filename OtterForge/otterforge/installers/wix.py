from __future__ import annotations

import os
from typing import Any

from ..models.installer_request import InstallerRequest
from .base import InstallerAdapter


class WixAdapter(InstallerAdapter):
    """WiX Toolset installer — Windows only, produces MSI packages."""

    name = "wix"
    supported_platforms = ("windows",)
    supported_formats = ("msi",)

    def _primary_tool(self) -> str:
        return "candle"

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": "WiX Toolset — build MSI packages from XML sources.",
            "platform": "Windows",
            "output_format": "MSI package (.msi)",
            "available": self.is_available(),
        }

    def installer_command(self, request: InstallerRequest) -> list[str]:
        # WiX requires two steps: candle (compile wxs) then light (link).
        # We return the candle step here; installer_runner calls both.
        wxs_files = [a for a in request.source_artifacts if a.endswith(".wxs")]
        cmd = ["candle"]
        if request.output_dir:
            cmd += ["-out", os.path.join(request.output_dir, "")]
        cmd += request.raw_installer_args
        cmd.extend(wxs_files)
        return cmd

    def light_command(self, request: InstallerRequest) -> list[str]:
        """Return the link step (candle → light) command."""
        out_name = (request.application_name or "setup").replace(" ", "_") + ".msi"
        wixobj_files = [
            os.path.join(request.output_dir, os.path.splitext(os.path.basename(a))[0] + ".wixobj")
            for a in request.source_artifacts
            if a.endswith(".wxs")
        ]
        cmd = ["light", "-out", os.path.join(request.output_dir, out_name)]
        cmd.extend(wixobj_files)
        return cmd

    def validate_request(self, request: InstallerRequest) -> list[str]:
        errors = super().validate_request(request)
        wxs = [a for a in request.source_artifacts if a.endswith(".wxs")]
        if not wxs:
            errors.append("wix: source_artifacts must contain at least one .wxs file")
        return errors
