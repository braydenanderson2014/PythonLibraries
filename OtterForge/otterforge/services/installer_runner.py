from __future__ import annotations

import os
import subprocess
from datetime import datetime

from ..models.installer_request import InstallerRequest
from ..models.installer_result import InstallerResult
from ..installers.registry import InstallerRegistry
from ..installers.wix import WixAdapter

_registry = InstallerRegistry()


class InstallerRunner:
    """Execute an installer adapter and return an InstallerResult."""

    def run(self, request: InstallerRequest) -> InstallerResult:
        # Resolve adapter
        installer_name = request.installer_name or _registry.resolve_installer()
        if not installer_name:
            return InstallerResult.failure("No installer available for the current platform.")

        adapter = _registry.get(installer_name)
        if adapter is None:
            return InstallerResult.failure(
                f"Unknown installer '{installer_name}'. "
                f"Available: {[i['name'] for i in _registry.list_all()]}",
                installer_name=installer_name,
            )

        # Validate
        errors = adapter.validate_request(request)
        if errors:
            return InstallerResult.failure(
                "; ".join(errors), installer_name=installer_name
            )

        # Build command
        cmd = adapter.installer_command(request)

        if request.dry_run:
            return InstallerResult(
                success=True,
                exit_code=0,
                final_command=cmd,
                stdout="[dry-run] no subprocess executed",
                installer_name=installer_name,
            )

        # Ensure output dir exists
        os.makedirs(request.output_dir, exist_ok=True)

        env = dict(os.environ)
        env.update(request.environment_overrides)

        started = datetime.utcnow()

        # For WiX we need two steps: candle then light
        if isinstance(adapter, WixAdapter):
            return self._run_wix(adapter, request, cmd, env, started, installer_name)

        try:
            proc = subprocess.run(
                cmd,
                cwd=request.project_path or None,
                env=env,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return InstallerResult.failure(
                f"Installer tool not found: {cmd[0]}",
                installer_name=installer_name,
            )

        finished = datetime.utcnow()
        duration = (finished - started).total_seconds()

        artifacts = self._collect_artifacts(request)

        return InstallerResult(
            success=proc.returncode == 0,
            exit_code=proc.returncode,
            final_command=cmd,
            artifact_paths=artifacts,
            stdout=proc.stdout,
            stderr=proc.stderr,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            duration_seconds=duration,
            installer_name=installer_name,
        )

    # ------------------------------------------------------------------
    # WiX two-step helper
    # ------------------------------------------------------------------

    def _run_wix(
        self,
        adapter: WixAdapter,
        request: InstallerRequest,
        candle_cmd: list[str],
        env: dict,
        started: datetime,
        installer_name: str,
    ) -> InstallerResult:
        try:
            candle_proc = subprocess.run(
                candle_cmd,
                cwd=request.project_path or None,
                env=env,
                capture_output=True,
                text=True,
            )
            if candle_proc.returncode != 0:
                finished = datetime.utcnow()
                return InstallerResult(
                    success=False,
                    exit_code=candle_proc.returncode,
                    final_command=candle_cmd,
                    stdout=candle_proc.stdout,
                    stderr=candle_proc.stderr,
                    started_at=started.isoformat(),
                    finished_at=finished.isoformat(),
                    duration_seconds=(finished - started).total_seconds(),
                    installer_name=installer_name,
                )

            light_cmd = adapter.light_command(request)
            light_proc = subprocess.run(
                light_cmd,
                cwd=request.project_path or None,
                env=env,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            return InstallerResult.failure(str(exc), installer_name=installer_name)

        finished = datetime.utcnow()
        combined_cmd = candle_cmd + ["&&"] + adapter.light_command(request)
        artifacts = self._collect_artifacts(request)

        return InstallerResult(
            success=light_proc.returncode == 0,
            exit_code=light_proc.returncode,
            final_command=combined_cmd,
            artifact_paths=artifacts,
            stdout=candle_proc.stdout + light_proc.stdout,
            stderr=candle_proc.stderr + light_proc.stderr,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            duration_seconds=(finished - started).total_seconds(),
            installer_name=installer_name,
        )

    # ------------------------------------------------------------------
    # Artifact collection
    # ------------------------------------------------------------------

    def _collect_artifacts(self, request: InstallerRequest) -> list[str]:
        output_dir = request.output_dir
        if not os.path.isdir(output_dir):
            return []
        exts = (".exe", ".msi", ".pkg", ".AppImage", ".deb", ".rpm")
        return [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if any(f.endswith(ext) for ext in exts)
        ]
