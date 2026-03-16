from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any


class TestRunnerGate:
    """Runs a project's test suite and optionally gates a build on success."""

    _SECTION = "test_configs"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _configs(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def set_config(
        self,
        state: dict[str, Any],
        project_path: str | Path,
        command: str,
        gate_enabled: bool = False,
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = {"command": command, "gate_enabled": gate_enabled}
        self._configs(state)[key] = cfg
        return cfg

    def get_config(
        self, state: dict[str, Any], project_path: str | Path
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = self._configs(state).get(key)
        if cfg is None:
            return {"error": f"No test config for '{key}'"}
        return cfg

    # --------------------------------------------------------------------- #
    # Test execution                                                          #
    # --------------------------------------------------------------------- #

    def run_tests(
        self,
        project_path: str | Path,
        command: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cwd = Path(project_path).resolve()
        if command is None and state is not None:
            cfg = self.get_config(state, project_path)
            command = cfg.get("command", "pytest")
        if not command:
            command = "pytest"

        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test run timed out after 300 seconds.",
                "duration": 300.0,
                "command": command,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(exc),
                "duration": round(time.monotonic() - start, 3),
                "command": command,
            }

        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration": round(time.monotonic() - start, 3),
            "command": command,
        }

    def gate_check(
        self,
        project_path: str | Path,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Run tests; block build if gate is enabled and tests fail."""
        cfg = self.get_config(state, project_path)
        if "error" in cfg:
            return {"gated": False, "skipped": True, "reason": cfg["error"]}

        gate_enabled = cfg.get("gate_enabled", False)
        result = self.run_tests(project_path, command=cfg.get("command"), state=state)

        if gate_enabled and not result["success"]:
            return {
                "gated": True,
                "blocked": True,
                "test_result": result,
            }
        return {
            "gated": gate_enabled,
            "blocked": False,
            "test_result": result,
        }
