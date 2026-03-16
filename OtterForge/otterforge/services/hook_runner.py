"""Hook runner service.

Hooks are user-defined shell commands that run at specific points in the
build lifecycle:

  - pre_build   : before the build command is executed
  - post_build  : after a build completes (regardless of success)
  - post_success: after a successful build
  - post_failure: after a failed build

Hooks are stored in the memory state under::

    memory["hooks"][project_key][event_type] = [
        {"command": "...", "shell": true/false, "name": "optional label"},
        ...
    ]

The project_key is the resolved absolute path of the project root as a string.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_EVENTS = ("pre_build", "post_build", "post_success", "post_failure")


@dataclass
class HookResult:
    event: str
    command: str
    name: str
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "name": self.name,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "success": self.success,
        }


class HookRunner:
    """Execute lifecycle hooks stored in memory state."""

    def __init__(self, memory: dict[str, Any]) -> None:
        self._memory = memory

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def _project_key(self, project_path: Path | str) -> str:
        return str(Path(project_path).resolve())

    def _hooks_root(self) -> dict[str, Any]:
        return self._memory.setdefault("hooks", {})

    def _project_hooks(self, project_path: Path | str) -> dict[str, list[dict[str, Any]]]:
        key = self._project_key(project_path)
        return self._hooks_root().setdefault(key, {})

    def add_hook(
        self,
        project_path: Path | str,
        event: str,
        command: str,
        name: str = "",
        shell: bool = True,
    ) -> dict[str, Any]:
        if event not in VALID_EVENTS:
            raise ValueError(f"Invalid event '{event}'. Must be one of {VALID_EVENTS}")
        hooks = self._project_hooks(project_path)
        entry: dict[str, Any] = {"command": command, "shell": shell, "name": name or command[:40]}
        hooks.setdefault(event, []).append(entry)
        return entry

    def list_hooks(self, project_path: Path | str) -> dict[str, list[dict[str, Any]]]:
        return dict(self._project_hooks(project_path))

    def remove_hook(self, project_path: Path | str, event: str, index: int) -> bool:
        hooks = self._project_hooks(project_path)
        event_hooks = hooks.get(event, [])
        if 0 <= index < len(event_hooks):
            event_hooks.pop(index)
            return True
        return False

    def clear_hooks(self, project_path: Path | str, event: str | None = None) -> None:
        hooks = self._project_hooks(project_path)
        if event:
            hooks.pop(event, None)
        else:
            hooks.clear()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_event(
        self,
        project_path: Path | str,
        event: str,
        cwd: Path | str | None = None,
    ) -> list[HookResult]:
        if event not in VALID_EVENTS:
            raise ValueError(f"Invalid event '{event}'")

        hooks = self._project_hooks(project_path).get(event, [])
        results: list[HookResult] = []

        for hook in hooks:
            cmd = hook["command"]
            use_shell = bool(hook.get("shell", True))
            label = str(hook.get("name", cmd[:40]))
            run_cwd = str(cwd or project_path)

            try:
                proc = subprocess.run(
                    cmd,
                    shell=use_shell,  # noqa: S602 – user-defined hook, intentional
                    capture_output=True,
                    text=True,
                    cwd=run_cwd,
                    check=False,
                )
                results.append(HookResult(
                    event=event,
                    command=cmd,
                    name=label,
                    returncode=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                ))
            except Exception as exc:
                results.append(HookResult(
                    event=event,
                    command=cmd,
                    name=label,
                    returncode=1,
                    stderr=str(exc),
                ))

        return results
