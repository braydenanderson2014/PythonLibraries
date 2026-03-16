from __future__ import annotations

from pathlib import Path


def resolve_project_root(project_root: Path | str | None = None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[2]


def resolve_data_dir(project_root: Path | str | None = None) -> Path:
    data_dir = resolve_project_root(project_root) / ".otterforge"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def resolve_runtime_config_path(project_root: Path | str | None = None) -> Path:
    return resolve_data_dir(project_root) / "runtime.json"


def resolve_sqlite_path(project_root: Path | str | None = None) -> Path:
    return resolve_data_dir(project_root) / "otterforge.db"