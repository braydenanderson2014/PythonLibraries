from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from .adapters.factory import AdapterRegistry
from .config_loader import ConfigError, load_config
from .pipeline import PipelineRunner


def execute_pipeline(
    config_path: Path,
    dry_run_override: bool | None = None,
    only_job: Optional[str] = None,
    plugins: Optional[Iterable[str]] = None,
) -> tuple[int, list[str]]:
    logs: list[str] = []

    try:
        ctx, jobs = load_config(config_path, dry_run_override=dry_run_override)
    except ConfigError as exc:
        return 2, [f"[config error] {exc}"]

    registry = AdapterRegistry()
    if plugins:
        for plugin in plugins:
            registry.register_plugin(plugin)

    runner = PipelineRunner(ctx, registry)

    try:
        results = runner.run_jobs(jobs, only=only_job)
    except Exception as exc:
        return 1, [f"[pipeline error] {exc}"]

    if not results:
        return 0, ["No jobs were executed."]

    for job, artifacts in results:
        mode = "DRY RUN" if ctx.dry_run else "EXECUTION"
        logs.append(f"=== {job.name} ({mode}) ===")
        logs.extend(artifacts.logs)
        logs.append(f"Final output: {artifacts.latest_media_file}")
        logs.append("")

    return 0, logs
