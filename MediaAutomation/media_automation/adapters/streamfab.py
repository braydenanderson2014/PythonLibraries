from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from .non_cli_web_ripper import launch_and_wait_for_download


class StreamFabAdapter(RipperAdapter):
    name = "streamfab"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("streamfab")
        if not exe:
            raise RuntimeError("StreamFab executable not configured. Set executables.streamfab in config.")
        return launch_and_wait_for_download("streamfab", exe, ctx, job, artifacts)
