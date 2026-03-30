from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from .non_cli_web_ripper import launch_and_wait_for_download


class VidicableAdapter(RipperAdapter):
    name = "vidicable"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("vidicable")
        if not exe:
            raise RuntimeError("Vidicable executable not configured. Set executables.vidicable in config.")
        return launch_and_wait_for_download("vidicable", exe, ctx, job, artifacts)
