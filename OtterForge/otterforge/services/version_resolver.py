"""Version resolver service.

Reads and writes version strings across the three canonical locations:
  1. ``pyproject.toml``  (``[project] version`` or ``[tool.poetry] version``)
  2. ``setup.cfg``       (``[metadata] version``)
  3. A ``__version__`` attribute in the main package source file

Also integrates with git to capture the current commit hash and detect dirty
state, and to create annotated version tags.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class VersionResolver:
    """Read and write version strings; capture git metadata."""

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def get_version(self, project_path: Path | str) -> dict[str, Any]:
        """Return version info gathered from the project."""
        path = Path(project_path)
        info: dict[str, Any] = {
            "pyproject_version": self._read_pyproject_version(path),
            "setup_cfg_version": self._read_setup_cfg_version(path),
            "source_version": self._read_source_version(path),
            "git": self._get_git_info(path),
        }
        # Derived "effective" version: prefer pyproject > setup.cfg > source > git tag
        info["effective_version"] = (
            info["pyproject_version"]
            or info["setup_cfg_version"]
            or info["source_version"]
            or (info["git"].get("latest_tag") if info["git"] else None)
        )
        return info

    def _read_pyproject_version(self, path: Path) -> str | None:
        toml_file = path / "pyproject.toml"
        if not toml_file.exists():
            return None
        try:
            content = toml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        # [project] version = "x.y.z"  OR  [tool.poetry] version = "x.y.z"
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        return match.group(1) if match else None

    def _read_setup_cfg_version(self, path: Path) -> str | None:
        cfg = path / "setup.cfg"
        if not cfg.exists():
            return None
        try:
            content = cfg.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        match = re.search(r'^version\s*=\s*(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _read_source_version(self, path: Path) -> str | None:
        """Search for ``__version__ = "x.y.z"`` in .py files under the project."""
        for py_file in path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                return match.group(1)
        return None

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def set_version(
        self,
        project_path: Path | str,
        new_version: str,
        targets: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """Write new_version to the requested targets (pyproject, setup_cfg, source).

        ``targets`` defaults to all three.  Returns a dict mapping
        target → list of paths updated.
        """
        path = Path(project_path)
        targets = targets or ["pyproject", "setup_cfg", "source"]
        updated: dict[str, list[str]] = {}

        if "pyproject" in targets:
            changed = self._write_pyproject_version(path, new_version)
            if changed:
                updated["pyproject"] = [str(path / "pyproject.toml")]

        if "setup_cfg" in targets:
            changed = self._write_setup_cfg_version(path, new_version)
            if changed:
                updated["setup_cfg"] = [str(path / "setup.cfg")]

        if "source" in targets:
            files = self._write_source_version(path, new_version)
            if files:
                updated["source"] = files

        return updated

    def _write_pyproject_version(self, path: Path, version: str) -> bool:
        toml_file = path / "pyproject.toml"
        if not toml_file.exists():
            return False
        content = toml_file.read_text(encoding="utf-8", errors="replace")
        new_content, n = re.subn(
            r'^(version\s*=\s*)["\'][^"\']*["\']',
            lambda m: f'{m.group(1)}"{version}"',
            content,
            flags=re.MULTILINE,
        )
        if n == 0:
            return False
        toml_file.write_text(new_content, encoding="utf-8")
        return True

    def _write_setup_cfg_version(self, path: Path, version: str) -> bool:
        cfg = path / "setup.cfg"
        if not cfg.exists():
            return False
        content = cfg.read_text(encoding="utf-8", errors="replace")
        new_content, n = re.subn(
            r'^(version\s*=\s*).+$',
            lambda m: f'{m.group(1)}{version}',
            content,
            flags=re.MULTILINE,
        )
        if n == 0:
            return False
        cfg.write_text(new_content, encoding="utf-8")
        return True

    def _write_source_version(self, path: Path, version: str) -> list[str]:
        updated: list[str] = []
        for py_file in path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            new_content, n = re.subn(
                r'^(__version__\s*=\s*)["\'][^"\']*["\']',
                lambda m: f'{m.group(1)}"{version}"',
                content,
                flags=re.MULTILINE,
            )
            if n > 0:
                py_file.write_text(new_content, encoding="utf-8")
                updated.append(str(py_file))
        return updated

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _run_git(self, args: list[str], cwd: Path) -> str | None:
        if shutil.which("git") is None:
            return None
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_git_info(self, path: Path) -> dict[str, Any] | None:
        if shutil.which("git") is None:
            return None
        commit = self._run_git(["rev-parse", "--short", "HEAD"], path)
        if commit is None:
            return None
        branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
        dirty_output = self._run_git(["status", "--porcelain"], path)
        dirty = bool(dirty_output)
        latest_tag = self._run_git(["describe", "--tags", "--abbrev=0"], path)
        return {
            "commit": commit,
            "branch": branch,
            "dirty": dirty,
            "latest_tag": latest_tag,
        }

    def create_git_tag(
        self,
        project_path: Path | str,
        tag: str,
        message: str = "",
        push: bool = False,
    ) -> dict[str, Any]:
        path = Path(project_path)
        if shutil.which("git") is None:
            return {"success": False, "error": "git not found"}

        tag_args = ["tag", "-a", tag, "-m", message or tag]
        result = subprocess.run(
            ["git"] + tag_args,
            capture_output=True,
            text=True,
            cwd=str(path),
            check=False,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}

        info: dict[str, Any] = {"success": True, "tag": tag}

        if push:
            push_result = subprocess.run(
                ["git", "push", "origin", tag],
                capture_output=True,
                text=True,
                cwd=str(path),
                check=False,
            )
            info["pushed"] = push_result.returncode == 0
            if not info["pushed"]:
                info["push_error"] = push_result.stderr.strip()

        return info
