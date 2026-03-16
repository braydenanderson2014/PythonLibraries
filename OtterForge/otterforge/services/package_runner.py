"""PackageRunner service — executes packaging operations."""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime

from otterforge.models.package_request import PackageRequest
from otterforge.models.package_result import PackageResult
from otterforge.packagers.registry import PackagerRegistry


class PackageRunner:
    def __init__(self, registry: PackagerRegistry | None = None) -> None:
        self.registry = registry or PackagerRegistry()

    def run(self, request: PackageRequest) -> PackageResult:
        started_at = datetime.now(UTC)

        # Resolve packager name
        packager_name = self.registry.resolve_packager(
            request.packager_name, request.project_path
        )
        adapter = self.registry.get(packager_name)

        adapter.validate_request(request)
        command = adapter.package_command(request)

        if request.dry_run:
            finished_at = datetime.now(UTC)
            return PackageResult(
                success=True,
                exit_code=0,
                final_command=command,
                artifact_paths=[],
                packager_name=packager_name,
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

        if not adapter.is_available():
            finished_at = datetime.now(UTC)
            return PackageResult(
                success=False,
                exit_code=1,
                final_command=command,
                stderr=f"Packager '{packager_name}' is not available on this system.",
                packager_name=packager_name,
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

        env = os.environ.copy()
        env.update(request.environment_overrides)
        output_dir = request.output_dir or (request.project_path / "dist")
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            proc = subprocess.run(
                command,
                cwd=str(request.project_path),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
        except FileNotFoundError as exc:
            finished_at = datetime.now(UTC)
            return PackageResult(
                success=False,
                exit_code=1,
                final_command=command,
                stderr=str(exc),
                packager_name=packager_name,
                started_at=started_at.isoformat(),
                finished_at=finished_at.isoformat(),
                duration_seconds=(finished_at - started_at).total_seconds(),
            )

        finished_at = datetime.now(UTC)
        artifact_paths = [
            str(p) for p in output_dir.iterdir()
            if p.suffix in (".whl", ".tar.gz", ".gz", ".zip", ".egg")
        ] if proc.returncode == 0 else []

        return PackageResult(
            success=proc.returncode == 0,
            exit_code=proc.returncode,
            final_command=command,
            artifact_paths=artifact_paths,
            stdout=proc.stdout,
            stderr=proc.stderr,
            packager_name=packager_name,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_seconds=(finished_at - started_at).total_seconds(),
        )
