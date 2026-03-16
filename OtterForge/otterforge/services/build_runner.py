from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime

from otterforge.builders.registry import BuilderRegistry
from otterforge.models.build_request import BuildRequest
from otterforge.models.build_result import BuildResult
from otterforge.services.command_translator import CommandTranslator


class BuildRunner:
    def __init__(self, translator: CommandTranslator | None = None) -> None:
        self.translator = translator or CommandTranslator(BuilderRegistry())

    def run(self, build_request: BuildRequest) -> BuildResult:
        started_at = datetime.now(UTC)
        command = self.translator.translate(build_request)
        adapter = self.translator.builder_registry.get(build_request.builder_name)

        if build_request.dry_run:
            finished_at = datetime.now(UTC)
            return BuildResult(
                success=True,
                exit_code=0,
                final_command=command,
                artifact_paths=[],
                stdout="",
                stderr="",
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
                builder_name=build_request.builder_name,
                target_platform=build_request.target_platform,
                environment_snapshot={"cwd": str(build_request.project_path.resolve())},
            )

        if not adapter.is_available():
            finished_at = datetime.now(UTC)
            return BuildResult(
                success=False,
                exit_code=1,
                final_command=command,
                stderr=f"Builder '{build_request.builder_name}' is not available on this system.",
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
                builder_name=build_request.builder_name,
                target_platform=build_request.target_platform,
                environment_snapshot={"cwd": str(build_request.project_path.resolve())},
            )

        environment = os.environ.copy()
        environment.update(build_request.environment_overrides)
        process = subprocess.run(
            command,
            cwd=build_request.project_path,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        finished_at = datetime.now(UTC)
        return BuildResult(
            success=process.returncode == 0,
            exit_code=process.returncode,
            final_command=command,
            stdout=process.stdout,
            stderr=process.stderr,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_seconds=(finished_at - started_at).total_seconds(),
            builder_name=build_request.builder_name,
            target_platform=build_request.target_platform,
            environment_snapshot={"cwd": str(build_request.project_path.resolve())},
        )