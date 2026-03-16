from __future__ import annotations

import shutil
import sys
from abc import ABC, abstractmethod
from typing import Any

from ..models.installer_request import InstallerRequest


class InstallerAdapter(ABC):
    """Base contract that every installer backend must implement."""

    name: str = ""
    supported_platforms: tuple[str, ...] = ("windows", "linux", "darwin")
    supported_formats: tuple[str, ...] = ()

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the required tool is present on PATH."""
        tool = self._primary_tool()
        return shutil.which(tool) is not None if tool else False

    @abstractmethod
    def _primary_tool(self) -> str:
        """Return the external executable that must be on PATH."""

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Return adapter metadata."""

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    @abstractmethod
    def installer_command(self, request: InstallerRequest) -> list[str]:
        """Build the subprocess command list for this request."""

    def validate_request(self, request: InstallerRequest) -> list[str]:
        """Return a list of validation error strings (empty = valid)."""
        errors: list[str] = []
        platform = sys.platform
        if "windows" not in self.supported_platforms and platform.startswith("win"):
            errors.append(f"{self.name} does not support Windows")
        if "linux" not in self.supported_platforms and platform.startswith("linux"):
            errors.append(f"{self.name} does not support Linux")
        if "darwin" not in self.supported_platforms and platform == "darwin":
            errors.append(f"{self.name} does not support macOS")
        return errors
