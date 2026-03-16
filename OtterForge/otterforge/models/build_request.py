from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BuildRequest:
    project_path: Path
    builder_name: str = "auto"
    language: str = "auto"
    target_platform: str = "current"
    entry_script: Path | None = None
    source_files: list[Path] = field(default_factory=list)
    executable_name: str | None = None
    mode: str = "onefile"
    console_mode: bool = True
    icon_path: Path | None = None
    splash_path: Path | None = None
    data_files: list[str] = field(default_factory=list)
    hidden_imports: list[str] = field(default_factory=list)
    extra_search_paths: list[str] = field(default_factory=list)
    output_dir: Path | None = None
    compiler: str | None = None
    standard: str | None = None
    optimization: str | None = None
    debug_symbols: bool = False
    include_paths: list[str] = field(default_factory=list)
    library_paths: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    compiler_config: dict[str, Any] = field(default_factory=dict)
    compiler_config_name: str | None = None
    clean: bool = False
    raw_builder_args: list[str] = field(default_factory=list)
    environment_overrides: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    profile_name: str | None = None
    project_schema_path: Path | None = None
    workflow_name: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BuildRequest":
        def to_path(value: Any) -> Path | None:
            if value in (None, ""):
                return None
            return Path(value)

        return cls(
            project_path=Path(payload.get("project_path", ".")),
            builder_name=str(payload.get("builder_name", "auto")),
            language=str(payload.get("language", payload.get("lang", "auto"))),
            target_platform=str(payload.get("target_platform", "current")),
            entry_script=to_path(payload.get("entry_script")),
            source_files=[Path(item) for item in payload.get("source_files", []) if item not in (None, "")],
            executable_name=payload.get("executable_name"),
            mode=str(payload.get("mode", "onefile")),
            console_mode=bool(payload.get("console_mode", True)),
            icon_path=to_path(payload.get("icon_path")),
            splash_path=to_path(payload.get("splash_path")),
            data_files=list(payload.get("data_files", [])),
            hidden_imports=list(payload.get("hidden_imports", [])),
            extra_search_paths=list(payload.get("extra_search_paths", [])),
            output_dir=to_path(payload.get("output_dir")),
            compiler=payload.get("compiler"),
            standard=payload.get("standard"),
            optimization=payload.get("optimization"),
            debug_symbols=bool(payload.get("debug_symbols", False)),
            include_paths=list(payload.get("include_paths", [])),
            library_paths=list(payload.get("library_paths", [])),
            libraries=list(payload.get("libraries", [])),
            compiler_config=dict(payload.get("compiler_config", {})),
            compiler_config_name=payload.get("compiler_config_name", payload.get("config_name")),
            clean=bool(payload.get("clean", False)),
            raw_builder_args=list(payload.get("raw_builder_args", [])),
            environment_overrides=dict(payload.get("environment_overrides", {})),
            dry_run=bool(payload.get("dry_run", False)),
            profile_name=payload.get("profile_name"),
            project_schema_path=to_path(payload.get("project_schema_path")),
            workflow_name=payload.get("workflow_name"),
        )