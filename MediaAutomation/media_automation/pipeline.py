from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from .adapters.factory import AdapterRegistry
from .models import JobArtifacts, JobConfig, PipelineContext
from .utils import ensure_dir


class PipelineRunner:
    def __init__(self, ctx: PipelineContext, registry: AdapterRegistry) -> None:
        self.ctx = ctx
        self.registry = registry

    def run_jobs(self, jobs: Iterable[JobConfig], only: Optional[str] = None) -> List[tuple[JobConfig, JobArtifacts]]:
        ensure_dir(self.ctx.output_root)
        ensure_dir(self.ctx.temp_root)

        results: List[tuple[JobConfig, JobArtifacts]] = []
        for job in jobs:
            if not job.enabled:
                continue
            if only and job.name != only:
                continue
            results.append((job, self.run_job(job)))
        return results

    def run_job(self, job: JobConfig) -> JobArtifacts:
        artifacts = JobArtifacts()

        ripper_order = self._resolve_ripper_order(job)
        ripper_errors: List[str] = []
        for ripper_name in ripper_order:
            try:
                artifacts.logs.append(f"[pipeline] trying ripper: {ripper_name}")
                ripper = self.registry.get_ripper(ripper_name)
                artifacts.ripped_file = ripper.rip(self.ctx, job, artifacts)
                artifacts.logs.append(f"[pipeline] ripper succeeded: {ripper_name}")
                break
            except Exception as exc:
                ripper_errors.append(f"{ripper_name}: {exc}")
                artifacts.logs.append(f"[pipeline] ripper failed: {ripper_name} -> {exc}")

        if artifacts.ripped_file is None:
            details = "; ".join(ripper_errors) if ripper_errors else "no ripper attempts"
            raise RuntimeError(f"All candidate rippers failed for job '{job.name}': {details}")

        subtitle = self.registry.maybe_get_subtitle(job.subtitle_adapter)
        if subtitle:
            artifacts.subtitled_file = subtitle.process(self.ctx, job, artifacts)

        encoder = self.registry.get_encoder(job.encoder)
        artifacts.encoded_file = encoder.encode(self.ctx, job, artifacts)

        return artifacts

    def _resolve_ripper_order(self, job: JobConfig) -> List[str]:
        if job.ripper_candidates:
            preferred = list(job.ripper_candidates)
        elif job.source_type.lower() == "online":
            raw_priority = self.ctx.defaults.get("online_ripper_priority", [])
            preferred = [str(x) for x in raw_priority] if isinstance(raw_priority, list) else []
            if job.ripper not in preferred:
                preferred.append(job.ripper)
        else:
            preferred = [job.ripper]

        deduped: List[str] = []
        for name in preferred:
            clean = name.strip()
            if clean and clean not in deduped:
                deduped.append(clean)
        return deduped or [job.ripper]
