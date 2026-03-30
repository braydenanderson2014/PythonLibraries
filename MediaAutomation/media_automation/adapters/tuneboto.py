from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from .non_cli_web_ripper import launch_and_wait_for_download


class TuneBotoAdapter(RipperAdapter):
    name = "tuneboto"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("tuneboto")
        if not exe:
            raise RuntimeError(
                "Tuneboto executable not configured. Set executables.tuneboto in config."
            )
        return launch_and_wait_for_download("tuneboto", exe, ctx, job, artifacts)
