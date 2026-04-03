from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from .non_cli_web_ripper import launch_and_wait_for_download


class FlixicamAdapter(RipperAdapter):
    name = "flixicam"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("flixicam")
        if not exe:
            raise RuntimeError("Flixicam executable not configured. Set executables.flixicam in config.")
        return launch_and_wait_for_download("flixicam", exe, ctx, job, artifacts)
