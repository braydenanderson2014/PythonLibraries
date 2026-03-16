"""Hatch packager adapter.

Uses ``hatch build`` to produce distribution packages from projects that use
Hatch / Hatchling as their build system.  Requires ``hatch`` to be installed.
"""
from __future__ import annotations

import shutil
import subprocess

from otterforge.models.package_request import PackageRequest
from otterforge.packagers.base import PackagerAdapter


class HatchPackagerAdapter(PackagerAdapter):
    @property
    def name(self) -> str:
        return "hatch"

    def get_supported_formats(self) -> list[str]:
        return ["wheel", "sdist", "all"]

    def is_available(self) -> bool:
        return shutil.which("hatch") is not None

    def get_version(self) -> str | None:
        if not self.is_available():
            return None
        result = subprocess.run(
            ["hatch", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return (result.stdout.strip() or result.stderr.strip()).splitlines()[0]

    def package_command(self, request: PackageRequest) -> list[str]:
        command = ["hatch", "build"]

        fmt = request.package_format.lower()
        if fmt == "wheel":
            command.extend(["-t", "wheel"])
        elif fmt == "sdist":
            command.extend(["-t", "sdist"])
        # "all" → omit -t flag

        if request.output_dir:
            command.extend(["-o", str(request.output_dir)])

        command.extend(request.raw_packager_args)
        return command
