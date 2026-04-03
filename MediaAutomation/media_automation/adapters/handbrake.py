from __future__ import annotations

from pathlib import Path

from ..interfaces import EncoderAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from ..utils import ensure_dir, quote_command, run_command


class HandBrakeAdapter(EncoderAdapter):
    name = "handbrake"

    def encode(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        input_file = artifacts.latest_media_file
        if input_file is None:
            raise RuntimeError(f"No input media available for encoding: {job.name}")

        exe = ctx.executables.get("handbrake", "HandBrakeCLI")
        out_dir = ctx.output_root / job.output_name
        ensure_dir(out_dir)

        output_file = out_dir / f"{job.output_name}.mp4"
        preset = ctx.defaults.get("handbrake_preset", "Fast 1080p30")

        cmd = [
            exe,
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--preset",
            preset,
        ]
        artifacts.logs.append(f"[handbrake] {quote_command(cmd)}")
        run_command(cmd, dry_run=ctx.dry_run)
        return output_file
