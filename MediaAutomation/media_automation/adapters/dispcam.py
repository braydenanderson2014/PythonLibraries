from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from .non_cli_web_ripper import launch_and_wait_for_download


class DispCamAdapter(RipperAdapter):
    name = "dispcam"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("dispcam")
        if not exe:
            raise RuntimeError("DispCam executable not configured. Set executables.dispcam in config.")
        return launch_and_wait_for_download("dispcam", exe, ctx, job, artifacts)
