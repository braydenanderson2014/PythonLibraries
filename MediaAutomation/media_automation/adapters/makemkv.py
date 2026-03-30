from __future__ import annotations

from pathlib import Path

from ..interfaces import RipperAdapter
from ..models import JobArtifacts, JobConfig, PipelineContext
from ..utils import ensure_dir, quote_command, run_command


class MakeMKVAdapter(RipperAdapter):
    name = "makemkv"

    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        exe = ctx.executables.get("makemkv", "makemkvcon64")
        out_dir = ctx.temp_root / job.output_name / "rip"
        ensure_dir(out_dir)

        title = job.title or "0"
        if job.source.startswith("disc:"):
            disc_id = job.source.split(":", 1)[1]
            source_arg = f"disc:{disc_id}"
        else:
            source_arg = job.source

        cmd = [exe, "mkv", source_arg, title, str(out_dir), "--decrypt"]
        artifacts.logs.append(f"[makemkv] {quote_command(cmd)}")
        run_command(cmd, dry_run=ctx.dry_run)

        expected_file = out_dir / f"{job.output_name}.mkv"
        artifacts.logs.append(f"[makemkv] expected output: {expected_file}")
        return expected_file
