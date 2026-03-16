from __future__ import annotations

from pathlib import Path
from typing import Any

from otterforge.builders.registry import BuilderRegistry
from otterforge.models.build_request import BuildRequest


class CommandTranslator:
    def __init__(self, builder_registry: BuilderRegistry | None = None) -> None:
        self.builder_registry = builder_registry or BuilderRegistry()

    def build_request_from_memory(
        self,
        memory_state: dict[str, Any],
        overrides: dict[str, Any] | None = None,
    ) -> BuildRequest:
        overrides = overrides or {}
        user_settings = memory_state.get("user_settings", {})
        payload = {
            "project_path": overrides.get("project_path") or user_settings.get("project_path") or ".",
            "builder_name": overrides.get("builder_name") or user_settings.get("default_builder") or "auto",
            "language": overrides.get("language") or user_settings.get("default_language") or "auto",
            "entry_script": overrides.get("entry_script") or user_settings.get("entry_script"),
            "source_files": overrides.get("source_files") or [],
            "executable_name": overrides.get("executable_name") or user_settings.get("app_name"),
            "mode": overrides.get("mode") or user_settings.get("build_mode") or "onefile",
            "console_mode": overrides.get("console_mode", user_settings.get("console_mode", True)),
            "icon_path": overrides.get("icon_path") or user_settings.get("icon_path"),
            "splash_path": overrides.get("splash_path") or user_settings.get("splash_path"),
            "output_dir": overrides.get("output_dir") or user_settings.get("output_dir"),
            "compiler": overrides.get("compiler") or user_settings.get("default_compiler"),
            "standard": overrides.get("standard") or user_settings.get("default_standard"),
            "optimization": overrides.get("optimization") or user_settings.get("default_optimization"),
            "debug_symbols": overrides.get("debug_symbols", user_settings.get("default_debug_symbols", False)),
            "include_paths": overrides.get("include_paths") or user_settings.get("default_include_paths", []),
            "library_paths": overrides.get("library_paths") or user_settings.get("default_library_paths", []),
            "libraries": overrides.get("libraries") or user_settings.get("default_libraries", []),
            "compiler_config": overrides.get("compiler_config") or {},
            "compiler_config_name": overrides.get("compiler_config_name") or overrides.get("config_name"),
            "clean": overrides.get("clean", user_settings.get("clean_build", False)),
            "raw_builder_args": overrides.get("raw_builder_args") or [],
            "dry_run": overrides.get("dry_run", False),
        }
        return BuildRequest.from_dict(payload)

    def translate(self, build_request: BuildRequest) -> list[str]:
        resolved_name = self.resolve_builder_name(build_request)
        build_request.builder_name = resolved_name
        adapter = self.builder_registry.get(resolved_name)
        return adapter.build_command(build_request)

    def resolve_builder_name(self, build_request: BuildRequest) -> str:
        configured = (build_request.builder_name or "").strip().lower()
        if configured and configured not in {"auto", "default"}:
            return configured

        explicit_language = self._normalize_language(build_request.language)
        if explicit_language and explicit_language != "auto":
            return self._builder_for_language(explicit_language)

        detected_language = self._detect_language(build_request)
        if detected_language is not None:
            return self._builder_for_language(detected_language)

        return "pyinstaller"

    def _detect_language(self, build_request: BuildRequest) -> str | None:
        candidate_paths: list[Path] = []
        if build_request.entry_script is not None:
            candidate_paths.append(build_request.entry_script)
        candidate_paths.extend(build_request.source_files)

        if not candidate_paths:
            return None

        suffix = candidate_paths[0].suffix.lower()
        if suffix == ".py":
            return "python"
        if suffix == ".c":
            return "c"
        if suffix in {".cc", ".cpp", ".cxx", ".hpp", ".hxx"}:
            return "cpp"
        if suffix == ".rs":
            return "rust"
        if suffix == ".go":
            return "go"
        return None

    def _builder_for_language(self, language: str) -> str:
        return {
            "python": "pyinstaller",
            "c": "c",
            "cpp": "cpp",
            "rust": "rust",
            "go": "go",
        }.get(language, "pyinstaller")

    def _normalize_language(self, language: str | None) -> str | None:
        if language is None:
            return None
        value = language.strip().lower()
        if value in {"", "auto"}:
            return "auto"
        if value in {"c++", "cplusplus"}:
            return "cpp"
        return value

    def inspect_builder(self, name: str) -> dict[str, object]:
        return self.builder_registry.inspect(name)

    def list_builders(self) -> list[dict[str, object]]:
        return self.builder_registry.list_builders()