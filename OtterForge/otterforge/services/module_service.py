from __future__ import annotations

import ast
import importlib.metadata
from pathlib import Path
import re
import sys
import tomllib
from typing import Any


IGNORED_PARTS = {".git", ".otterforge", "__pycache__", ".pytest_cache", ".venv", "venv"}

IMPORT_DISTRIBUTION_ALIASES = {
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "cv2": "opencv-python",
}


class ModuleService:
    def list_modules(self, path: str | Path = ".") -> dict[str, Any]:
        root = Path(path).resolve()
        pyproject_summary = self._read_pyproject(root / "pyproject.toml")
        requirements_summary = self._read_requirements_files(root)
        imports_summary = self._scan_python_imports(root)

        all_modules: set[str] = set()
        all_modules.update(pyproject_summary.get("dependencies", []))
        for values in pyproject_summary.get("optional_dependencies", {}).values():
            all_modules.update(values)
        for req_file in requirements_summary:
            all_modules.update(req_file["modules"])

        inferred_modules = set(imports_summary.get("inferred_modules", []))
        dependency_inventory = self._build_dependency_inventory(
            declared_specs=sorted(all_modules),
            inferred_modules=sorted(inferred_modules),
        )

        return {
            "project_root": str(root),
            "pyproject": pyproject_summary,
            "requirements": requirements_summary,
            "all_modules": sorted(all_modules),
            "imports": imports_summary,
            "dependency_inventory": dependency_inventory,
            "missing_dependencies": [
                item["name"] for item in dependency_inventory if not item.get("installed", False)
            ],
        }

    def _read_pyproject(self, pyproject_path: Path) -> dict[str, Any]:
        if not pyproject_path.exists():
            return {
                "path": str(pyproject_path),
                "exists": False,
                "dependencies": [],
                "optional_dependencies": {},
            }

        with pyproject_path.open("rb") as handle:
            data = tomllib.load(handle)

        project = data.get("project", {})
        dependencies = [str(item) for item in project.get("dependencies", [])]
        optional_dependencies = {
            str(key): [str(item) for item in values]
            for key, values in project.get("optional-dependencies", {}).items()
        }

        return {
            "path": str(pyproject_path),
            "exists": True,
            "dependencies": dependencies,
            "optional_dependencies": optional_dependencies,
        }

    def _read_requirements_files(self, root: Path) -> list[dict[str, Any]]:
        files = sorted(root.glob("requirements*.txt"))
        summaries: list[dict[str, Any]] = []

        for file_path in files:
            modules: list[str] = []
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    parsed = self._parse_requirement_line(line)
                    if parsed is not None:
                        modules.append(parsed)
            summaries.append(
                {
                    "path": str(file_path),
                    "modules": modules,
                }
            )

        return summaries

    def _parse_requirement_line(self, raw_line: str) -> str | None:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return None
        if line.startswith(("-r ", "--requirement ", "-c ", "--constraint ")):
            return None
        return line

    def _scan_python_imports(self, root: Path) -> dict[str, Any]:
        records: dict[str, set[str]] = {}
        files_scanned = 0
        stdlib = set(getattr(sys, "stdlib_module_names", set()))
        local_modules = self._discover_local_modules(root)

        for candidate in root.rglob("*.py"):
            if any(part in IGNORED_PARTS for part in candidate.parts):
                continue
            files_scanned += 1
            try:
                source = candidate.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            for node in ast.walk(tree):
                module_name = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".", 1)[0].strip()
                        if module_name:
                            records.setdefault(module_name, set()).add(str(candidate))
                elif isinstance(node, ast.ImportFrom):
                    if node.level and not node.module:
                        continue
                    if node.module:
                        module_name = node.module.split(".", 1)[0].strip()
                        if module_name:
                            records.setdefault(module_name, set()).add(str(candidate))

        inferred = []
        for name, files in records.items():
            if not name:
                continue
            if name in stdlib or name in {"typing", "pathlib", "dataclasses"}:
                continue
            if name in local_modules:
                continue
            inferred.append(
                {
                    "name": name,
                    "source_files": sorted(files),
                }
            )

        inferred_sorted = sorted(inferred, key=lambda item: str(item["name"]))
        return {
            "files_scanned": files_scanned,
            "inferred": inferred_sorted,
            "inferred_modules": [item["name"] for item in inferred_sorted],
        }

    def _discover_local_modules(self, root: Path) -> set[str]:
        names: set[str] = set()

        for candidate in root.rglob("*.py"):
            if any(part in IGNORED_PARTS for part in candidate.parts):
                continue
            if candidate.name == "__init__.py":
                names.add(candidate.parent.name)
            else:
                names.add(candidate.stem)

        return {name for name in names if name}

    def _build_dependency_inventory(
        self,
        declared_specs: list[str],
        inferred_modules: list[str],
    ) -> list[dict[str, Any]]:
        declared_names = {self._extract_requirement_name(spec): spec for spec in declared_specs}
        candidates: set[str] = set(declared_names.keys())
        candidates.update(inferred_modules)

        inventory: list[dict[str, Any]] = []
        for name in sorted(item for item in candidates if item):
            version = self._detect_installed_version(name)
            declared_spec = declared_names.get(name)
            inventory.append(
                {
                    "name": name,
                    "declared_spec": declared_spec,
                    "installed": version is not None,
                    "installed_version": version,
                    "source": "declared" if declared_spec else "inferred",
                }
            )
        return inventory

    def _extract_requirement_name(self, requirement: str) -> str:
        cleaned = requirement.strip()
        if not cleaned:
            return ""
        if cleaned.startswith("git+") or cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned
        match = re.match(r"^[A-Za-z0-9_.-]+", cleaned)
        if not match:
            return cleaned
        return match.group(0).replace("-", "_")

    def _detect_installed_version(self, package_name: str) -> str | None:
        alias_name = IMPORT_DISTRIBUTION_ALIASES.get(package_name)
        if alias_name:
            try:
                return importlib.metadata.version(alias_name)
            except importlib.metadata.PackageNotFoundError:
                pass

        normalized = package_name.replace("_", "-")
        try:
            return importlib.metadata.version(normalized)
        except importlib.metadata.PackageNotFoundError:
            try:
                return importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError:
                return None
