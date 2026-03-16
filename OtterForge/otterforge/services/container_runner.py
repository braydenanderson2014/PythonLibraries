from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


class ContainerRunner:
    """Run a build command inside a Docker container.

    The project directory is mounted as a volume so that artifact output
    files are written back to the host via the same mount.
    """

    _SECTION = "container_configs"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _configs(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def set_config(
        self,
        state: dict[str, Any],
        project_path: str | Path,
        image: str,
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = {"image": image}
        self._configs(state)[key] = cfg
        return cfg

    def get_config(
        self, state: dict[str, Any], project_path: str | Path
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = self._configs(state).get(key)
        if cfg is None:
            return {"error": f"No container config for '{key}'"}
        return cfg

    # --------------------------------------------------------------------- #
    # Availability                                                            #
    # --------------------------------------------------------------------- #

    def is_available(self) -> bool:
        return shutil.which("docker") is not None

    # --------------------------------------------------------------------- #
    # Build                                                                   #
    # --------------------------------------------------------------------- #

    def run_build(
        self,
        project_path: str | Path,
        build_command: str,
        state: dict[str, Any],
        image: str | None = None,
        output_dir: str = "dist",
    ) -> dict[str, Any]:
        if not self.is_available():
            return {
                "success": False,
                "error": "Docker is not available on PATH. Install Docker Desktop or Docker Engine.",
            }

        cwd = Path(project_path).resolve()
        cfg = self.get_config(state, project_path)
        resolved_image = image or cfg.get("image")
        if not resolved_image:
            return {
                "success": False,
                "error": "No Docker image specified. Set one with 'otterforge set build.container_image <image>'.",
            }

        # Mount project dir to /workspace inside the container
        mount = f"{cwd}:/workspace"
        workdir = "/workspace"

        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            mount,
            "-w",
            workdir,
            resolved_image,
            "sh",
            "-c",
            build_command,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Container build timed out after 600 seconds.",
                "image": resolved_image,
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "image": resolved_image}

        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "image": resolved_image,
            "command": build_command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output_dir": str(cwd / output_dir),
        }
