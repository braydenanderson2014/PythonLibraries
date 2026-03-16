from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

_SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


class DependencyAuditor:
    """Audit project dependencies for known vulnerabilities.

    Primary tool: pip-audit.  Fallback: safety.
    """

    _SECTION = "audit_configs"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _configs(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def set_config(
        self,
        state: dict[str, Any],
        project_path: str | Path,
        gate_enabled: bool = False,
        min_severity: str = "high",
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = {"gate_enabled": gate_enabled, "min_severity": min_severity}
        self._configs(state)[key] = cfg
        return cfg

    def get_config(
        self, state: dict[str, Any], project_path: str | Path
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = self._configs(state).get(key)
        if cfg is None:
            return {"error": f"No audit config for '{key}'"}
        return cfg

    # --------------------------------------------------------------------- #
    # Audit execution                                                         #
    # --------------------------------------------------------------------- #

    def run_audit(
        self,
        project_path: str | Path,
        requirements_file: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cwd = Path(project_path).resolve()
        tool = self._pick_tool()

        if tool is None:
            return {
                "success": False,
                "tool": None,
                "vulnerabilities": [],
                "error": (
                    "Neither pip-audit nor safety is available on PATH. "
                    "Install one with: pip install pip-audit"
                ),
            }

        vulns, raw_error = self._run_tool(tool, cwd, requirements_file)
        cfg = self.get_config(state, project_path) if state else {}
        gate_enabled = cfg.get("gate_enabled", False)
        min_severity = cfg.get("min_severity", "high")

        blocked = gate_enabled and self._exceeds_threshold(vulns, min_severity)

        return {
            "success": raw_error is None,
            "tool": tool,
            "vulnerabilities": vulns,
            "count": len(vulns),
            "gate_enabled": gate_enabled,
            "min_severity": min_severity,
            "blocked": blocked,
            "error": raw_error,
        }

    # --------------------------------------------------------------------- #
    # Internal                                                                #
    # --------------------------------------------------------------------- #

    def _pick_tool(self) -> str | None:
        if shutil.which("pip-audit"):
            return "pip-audit"
        if shutil.which("safety"):
            return "safety"
        return None

    def _run_tool(
        self,
        tool: str,
        cwd: Path,
        requirements_file: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        if tool == "pip-audit":
            return self._run_pip_audit(cwd, requirements_file)
        return self._run_safety(cwd, requirements_file)

    def _run_pip_audit(
        self, cwd: Path, requirements_file: str | None
    ) -> tuple[list[dict[str, Any]], str | None]:
        cmd = ["pip-audit", "--format", "json"]
        if requirements_file:
            cmd += ["-r", requirements_file]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(cwd), timeout=120
            )
        except Exception as exc:  # noqa: BLE001
            return [], str(exc)

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            if result.returncode == 0:
                return [], None
            return [], result.stderr or "pip-audit returned no JSON"

        vulns: list[dict[str, Any]] = []
        for dep in data.get("dependencies", []):
            for vuln in dep.get("vulns", []):
                vulns.append(
                    {
                        "package": dep.get("name", ""),
                        "version": dep.get("version", ""),
                        "vuln_id": vuln.get("id", ""),
                        "aliases": vuln.get("aliases", []),
                        "description": vuln.get("description", ""),
                        "severity": vuln.get("severity", "unknown"),
                        "fix_versions": vuln.get("fix_versions", []),
                    }
                )
        return vulns, None

    def _run_safety(
        self, cwd: Path, requirements_file: str | None
    ) -> tuple[list[dict[str, Any]], str | None]:
        cmd = ["safety", "check", "--json"]
        if requirements_file:
            cmd += ["-r", requirements_file]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(cwd), timeout=120
            )
        except Exception as exc:  # noqa: BLE001
            return [], str(exc)

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            if result.returncode == 0:
                return [], None
            return [], result.stderr or "safety returned no JSON"

        vulns: list[dict[str, Any]] = []
        for item in (data if isinstance(data, list) else []):
            vulns.append(
                {
                    "package": item[0] if len(item) > 0 else "",
                    "version": item[2] if len(item) > 2 else "",
                    "vuln_id": item[4] if len(item) > 4 else "",
                    "description": item[3] if len(item) > 3 else "",
                    "severity": "unknown",
                }
            )
        return vulns, None

    def _exceeds_threshold(
        self, vulns: list[dict[str, Any]], min_severity: str
    ) -> bool:
        threshold_idx = _SEVERITY_ORDER.index(min_severity) if min_severity in _SEVERITY_ORDER else len(_SEVERITY_ORDER)
        for v in vulns:
            sev = str(v.get("severity", "info")).lower()
            if sev in _SEVERITY_ORDER:
                if _SEVERITY_ORDER.index(sev) <= threshold_idx:
                    return True
        return False
