from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from otterforge.builders.base import ToolAdapter
from otterforge.models.build_request import BuildRequest


class CBuilderAdapter(ToolAdapter):
    @property
    def name(self) -> str:
        return "c"

    def get_language_family(self) -> str:
        return "c"

    def is_available(self) -> bool:
        return any(shutil.which(candidate) is not None for candidate in self._candidates())

    def get_version(self) -> str | None:
        compiler = self._first_available_compiler()
        if compiler is None:
            return None
        result = subprocess.run(
            [compiler, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip() or result.stderr.strip()
        return output.splitlines()[0] if output else None

    def get_supported_common_options(self) -> list[str]:
        return [
            "entry_script",
            "source_files",
            "executable_name",
            "output_dir",
            "compiler",
            "standard",
            "optimization",
            "debug_symbols",
            "include_paths",
            "library_paths",
            "libraries",
            "raw_builder_args",
            "compiler_config",
        ]

    def validate_request(self, build_request: BuildRequest) -> None:
        sources = self._collect_source_files(build_request)
        if not sources:
            raise ValueError("At least one C source is required via entry_script or source_files")

        missing = [str(path) for path in sources if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Source file(s) not found: {', '.join(missing)}")

    def build_command(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)

        compiler = self._resolve_compiler(build_request)
        command = [compiler]

        standard = self._setting(build_request, "standard")
        if standard:
            command.append(f"-std={standard}")

        optimization = self._setting(build_request, "optimization")
        if optimization:
            opt = str(optimization)
            command.append(opt if opt.startswith("-O") else f"-O{opt}")

        debug_symbols = self._bool_setting(build_request, "debug_symbols")
        if debug_symbols:
            command.append("-g")

        for include_path in self._list_setting(build_request, "include_paths"):
            command.extend(["-I", include_path])

        for library_path in self._list_setting(build_request, "library_paths"):
            command.extend(["-L", library_path])

        for library in self._list_setting(build_request, "libraries"):
            command.extend(["-l", library])

        output_name = build_request.executable_name or self._collect_source_files(build_request)[0].stem
        if build_request.output_dir:
            output_path = build_request.output_dir / output_name
        else:
            output_path = Path(output_name)
        command.extend(["-o", str(output_path)])

        command.extend(str(path) for path in self._collect_source_files(build_request))
        command.extend(build_request.raw_builder_args)
        return command

    def _candidates(self) -> list[str]:
        return ["gcc", "clang", "cc"]

    def _first_available_compiler(self) -> str | None:
        for candidate in self._candidates():
            if shutil.which(candidate) is not None:
                return candidate
        return None

    def _resolve_compiler(self, build_request: BuildRequest) -> str:
        explicit = self._setting(build_request, "compiler")
        if explicit:
            return str(explicit)
        return self._first_available_compiler() or self._candidates()[0]

    def _collect_source_files(self, build_request: BuildRequest) -> list[Path]:
        sources = list(build_request.source_files)
        if build_request.entry_script is not None and build_request.entry_script not in sources:
            sources.insert(0, build_request.entry_script)
        return sources

    def _setting(self, build_request: BuildRequest, key: str) -> str | bool | None:
        direct = getattr(build_request, key)
        if direct not in (None, "", []):
            return direct
        value = build_request.compiler_config.get(key)
        if value in (None, "", []):
            return None
        return value

    def _bool_setting(self, build_request: BuildRequest, key: str) -> bool:
        direct = bool(getattr(build_request, key))
        if direct:
            return True
        return bool(build_request.compiler_config.get(key, False))

    def _list_setting(self, build_request: BuildRequest, key: str) -> list[str]:
        direct = list(getattr(build_request, key))
        if direct:
            return [str(item) for item in direct]
        from_config = build_request.compiler_config.get(key, [])
        if isinstance(from_config, list):
            return [str(item) for item in from_config]
        return []
