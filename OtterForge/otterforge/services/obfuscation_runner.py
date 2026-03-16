from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime

from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.models.obfuscation_result import ObfuscationResult
from otterforge.obfuscators.registry import ObfuscatorRegistry


class ObfuscationRunner:
    def __init__(self, registry: ObfuscatorRegistry | None = None) -> None:
        self.registry = registry or ObfuscatorRegistry()

    def run(self, request: ObfuscationRequest) -> ObfuscationResult:
        started_at = datetime.now(UTC)
        adapter = self.registry.get(request.tool_name)
        command = adapter.build_command(request)
        source = request.source_path or request.project_path

        if request.dry_run:
            finished_at = datetime.now(UTC)
            return ObfuscationResult(
                success=True,
                exit_code=0,
                final_command=command,
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
                tool_name=request.tool_name,
                output_path=str(request.output_dir) if request.output_dir else None,
                environment_snapshot={"cwd": str(source.parent.resolve())},
            )

        if not adapter.is_available():
            finished_at = datetime.now(UTC)
            return ObfuscationResult(
                success=False,
                exit_code=1,
                final_command=command,
                stderr=f"Obfuscation tool '{request.tool_name}' is not available on this system.",
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
                tool_name=request.tool_name,
                output_path=str(request.output_dir) if request.output_dir else None,
                environment_snapshot={"cwd": str(source.parent.resolve())},
            )

        environment = os.environ.copy()
        environment.update(request.environment_overrides)
        process = subprocess.run(
            command,
            cwd=source.parent,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        finished_at = datetime.now(UTC)
        return ObfuscationResult(
            success=process.returncode == 0,
            exit_code=process.returncode,
            final_command=command,
            stdout=process.stdout,
            stderr=process.stderr,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_seconds=(finished_at - started_at).total_seconds(),
            tool_name=request.tool_name,
            output_path=str(request.output_dir) if request.output_dir else None,
            environment_snapshot={"cwd": str(source.parent.resolve())},
        )
