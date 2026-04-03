from __future__ import annotations

from pathlib import Path

from ..interfaces import SubtitleAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from ..utils import ensure_dir, quote_command, run_command


class SubtitleToolAdapter(SubtitleAdapter):
    name = "subtitle_tool"

    def process(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        input_file = artifacts.latest_media_file
        if input_file is None:
            raise RuntimeError(f"No media available for subtitle processing: {job.name}")

        exe = ctx.executables.get("subtitle_tool", "python")
        subtitle_profile = ctx.defaults.get("subtitle_profile", "default")
        out_dir = ctx.temp_root / job.output_name / "subtitles"
        ensure_dir(out_dir)

        output_file = out_dir / f"{job.output_name}.subtitled.mkv"

        cmd = [
            exe,
            "Subtitle/main.py",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--profile",
            str(subtitle_profile),
        ]
        artifacts.logs.append(f"[subtitle_tool] {quote_command(cmd)}")
        run_command(cmd, dry_run=ctx.dry_run)
        return output_file
