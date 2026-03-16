from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class SigningService:
    """Post-build code signing using platform-appropriate tools.

    Adapters:
      - signtool  (Windows)
      - codesign  (macOS)
      - gpg       (cross-platform, detached .sig)
    """

    _SECTION = "signing_configs"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _configs(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def set_config(
        self,
        state: dict[str, Any],
        project_path: str | Path,
        tool: str,
        *,
        cert: str = "",
        timestamp_url: str = "",
        developer_id: str = "",
        key_id: str = "",
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        existing = self._configs(state).get(key, {})
        cfg = {
            "tool": tool or existing.get("tool", ""),
            "cert": cert if cert else existing.get("cert", ""),
            "timestamp_url": timestamp_url if timestamp_url else existing.get("timestamp_url", ""),
            "developer_id": developer_id if developer_id else existing.get("developer_id", ""),
            "key_id": key_id if key_id else existing.get("key_id", ""),
        }
        self._configs(state)[key] = cfg
        # Return without sensitive cert path — callers should not log it either
        return {"tool": cfg["tool"], "configured": True}

    def get_config(
        self, state: dict[str, Any], project_path: str | Path
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = self._configs(state).get(key)
        if cfg is None:
            return {"error": f"No signing config for '{key}'"}
        # Redact cert path from return value
        return {k: v for k, v in cfg.items() if k != "cert"}

    # --------------------------------------------------------------------- #
    # Signing                                                                 #
    # --------------------------------------------------------------------- #

    def sign_artifacts(
        self,
        project_path: str | Path,
        artifact_paths: list[str],
        state: dict[str, Any],
        tool: str | None = None,
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        cfg = self._configs(state).get(key, {})
        resolved_tool = tool or cfg.get("tool") or self._default_tool()

        results: list[dict[str, Any]] = []
        for art in artifact_paths:
            result = self._sign_one(Path(art), resolved_tool, cfg)
            results.append(result)

        return {
            "tool": resolved_tool,
            "signed": [r["path"] for r in results if r.get("success")],
            "failed": [r["path"] for r in results if not r.get("success")],
            "details": results,
        }

    # --------------------------------------------------------------------- #
    # Internal                                                                #
    # --------------------------------------------------------------------- #

    def _default_tool(self) -> str:
        if sys.platform.startswith("win"):
            return "signtool"
        if sys.platform == "darwin":
            return "codesign"
        return "gpg"

    def _tool_available(self, tool: str) -> bool:
        lookup = {"signtool": "signtool", "codesign": "codesign", "gpg": "gpg"}
        exe = lookup.get(tool, tool)
        return shutil.which(exe) is not None

    def _sign_one(
        self, artifact: Path, tool: str, cfg: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._tool_available(tool):
            return {
                "path": str(artifact),
                "success": False,
                "warning": f"Signing tool '{tool}' not found on PATH — artifact unsigned.",
            }

        try:
            if tool == "signtool":
                return self._signtool(artifact, cfg)
            if tool == "codesign":
                return self._codesign(artifact, cfg)
            if tool == "gpg":
                return self._gpg(artifact, cfg)
        except Exception as exc:  # noqa: BLE001
            return {"path": str(artifact), "success": False, "error": str(exc)}

        return {"path": str(artifact), "success": False, "error": f"Unknown tool: {tool}"}

    def _signtool(self, artifact: Path, cfg: dict[str, Any]) -> dict[str, Any]:
        cmd = ["signtool", "sign"]
        cert = cfg.get("cert", "")
        if cert:
            cmd += ["/f", cert]
        ts = cfg.get("timestamp_url", "")
        if ts:
            cmd += ["/tr", ts, "/td", "sha256"]
        cmd.append(str(artifact))
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "path": str(artifact),
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _codesign(self, artifact: Path, cfg: dict[str, Any]) -> dict[str, Any]:
        dev_id = cfg.get("developer_id", "")
        cmd = ["codesign", "--force", "--deep"]
        if dev_id:
            cmd += ["--sign", dev_id]
        else:
            cmd += ["--sign", "-"]  # ad-hoc signing
        cmd.append(str(artifact))
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "path": str(artifact),
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _gpg(self, artifact: Path, cfg: dict[str, Any]) -> dict[str, Any]:
        cmd = ["gpg", "--detach-sign", "--armor"]
        key_id = cfg.get("key_id", "")
        if key_id:
            cmd += ["--local-user", key_id]
        cmd.append(str(artifact))
        result = subprocess.run(cmd, capture_output=True, text=True)
        sig_path = str(artifact) + ".asc"
        return {
            "path": str(artifact),
            "sig_path": sig_path,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
