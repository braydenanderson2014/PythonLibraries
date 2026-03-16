"""Poetry packager adapter.

Uses ``poetry build`` to produce wheels and sdists from projects that use
Poetry as their dependency and packaging manager.
"""
from __future__ import annotations

import shutil
import subprocess

from otterforge.models.package_request import PackageRequest
from otterforge.packagers.base import PackagerAdapter


class PoetryPackagerAdapter(PackagerAdapter):
    @property
    def name(self) -> str:
        return "poetry"

    def get_supported_formats(self) -> list[str]:
        return ["wheel", "sdist", "all"]

    def is_available(self) -> bool:
        return shutil.which("poetry") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["poetry", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return (result.stdout.strip() or result.stderr.strip()).splitlines()[0]

    def package_command(self, request: PackageRequest) -> list[str]:
        command = ["poetry", "build"]

        fmt = request.package_format.lower()
        if fmt == "wheel":
            command.extend(["--format", "wheel"])
        elif fmt == "sdist":
            command.extend(["--format", "sdist"])
        # "all" → omit --format flag

        command.extend(request.raw_packager_args)
        return command
