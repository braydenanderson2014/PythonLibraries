from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import JobConfig, PipelineContext


class ConfigError(RuntimeError):
    pass


def create_starter_config(config_path: Path) -> bool:
    target = config_path.expanduser().resolve()
    if target.exists():
        return False

    target.parent.mkdir(parents=True, exist_ok=True)

    starter: Dict[str, Any] = {
        "paths": {
            "output_root": "./output",
            "temp_root": "./temp",
        },
        "executables": {
            "makemkv": "",
            "handbrake": "",
            "subtitle_tool": "python",
            "tuneboto": "",
            "vidicable": "",
            "dispcam": "",
            "flixicam": "",
            "streamfab": "",
        },
        "defaults": {
            "dry_run": True,
            "rip_format": "mkv",
            "handbrake_preset": "Fast 1080p30",
            "subtitle_profile": "default",
            "online_ripper_priority": [
                "vidicable",
                "dispcam",
                "flixicam",
                "streamfab",
                "tuneboto",
            ],
            "download_watch_dir": "D:/Downloads",
            "download_timeout_sec": 1800,
            "download_stable_for_sec": 8,
            "download_extensions": [".mkv", ".mp4"],
            "launch_with_source_url": True,
            "first_use_signin_required": True,
            "first_use_signin_wait_sec": 45,
        },
        "jobs": [],
    }

    target.write_text(json.dumps(starter, indent=2) + "\n", encoding="utf-8")
    return True


def load_config(config_path: Path, dry_run_override: bool | None = None) -> tuple[PipelineContext, List[JobConfig]]:
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    raw: Dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    paths = raw.get("paths", {})
    executables = raw.get("executables", {})
    defaults = raw.get("defaults", {})

    if "output_root" not in paths or "temp_root" not in paths:
        raise ConfigError("Config requires paths.output_root and paths.temp_root")

    dry_run = defaults.get("dry_run", True)
    if dry_run_override is not None:
        dry_run = dry_run_override

    ctx = PipelineContext(
        dry_run=bool(dry_run),
        output_root=Path(paths["output_root"]).expanduser().resolve(),
        temp_root=Path(paths["temp_root"]).expanduser().resolve(),
        executables=executables,
        defaults=defaults,
    )

    jobs: List[JobConfig] = []
    for item in raw.get("jobs", []):
        raw_candidates = item.get("ripper_candidates", [])
        ripper_candidates = [str(x) for x in raw_candidates] if isinstance(raw_candidates, list) else []
        jobs.append(
            JobConfig(
                name=item["name"],
                enabled=bool(item.get("enabled", True)),
                source_type=item.get("source_type", "file"),
                source=item["source"],
                output_name=item["output_name"],
                ripper=item["ripper"],
                encoder=item["encoder"],
                ripper_candidates=ripper_candidates,
                subtitle_adapter=item.get("subtitle_adapter"),
                title=item.get("title"),
                metadata=item.get("metadata", {}),
            )
        )

    return ctx, jobs
