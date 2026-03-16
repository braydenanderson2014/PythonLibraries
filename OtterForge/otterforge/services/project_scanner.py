from __future__ import annotations

import ast
from pathlib import Path
import tomllib


ICON_EXTENSIONS = {".ico", ".icns", ".png", ".svg", ".bmp"}
SPLASH_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".bmp", ".gif"}
DOC_EXTENSIONS = {".md", ".txt", ".rst", ".docx", ".pdf"}
IGNORED_PARTS = {".git", ".otterforge", "__pycache__", ".pytest_cache", ".venv", "venv"}
IGNORED_EXTENSIONS = {".pyc", ".pyo"}


class ProjectScanner:
    def discover(
        self,
        path: str | Path,
        scope: str = "projects",
        include_extensions: list[str] | None = None,
    ) -> dict[str, object]:
        root = Path(path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Scan target does not exist: {root}")

        normalized_extensions = None
        if include_extensions:
            normalized_extensions = {
                item if item.startswith(".") else f".{item}" for item in include_extensions
            }

        files = []
        entry_points = []
        spec_files = []
        pyproject_entry_hints = self._entry_points_from_pyproject(root)

        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            if any(part in IGNORED_PARTS for part in candidate.parts):
                continue
            if candidate.suffix.lower() in IGNORED_EXTENSIONS:
                continue
            if normalized_extensions and candidate.suffix.lower() not in normalized_extensions:
                continue

            role, confidence = self._classify(candidate, root=root, pyproject_entry_hints=pyproject_entry_hints)
            record = {
                "path": str(candidate),
                "name": candidate.name,
                "extension": candidate.suffix.lower(),
                "role": role,
                "confidence": confidence,
                "suggested_target_folder": self._target_folder(role),
            }
            files.append(record)

            if record["extension"] == ".spec":
                spec_files.append(str(candidate))
            if self._is_entry_point(candidate, root=root, pyproject_entry_hints=pyproject_entry_hints):
                entry_points.append(str(candidate))

        return {
            "path": str(root),
            "scope": scope,
            "entry_points": sorted(entry_points),
            "spec_files": sorted(spec_files),
            "files": sorted(files, key=lambda item: item["path"]),
        }

    def _classify(
        self,
        path: Path,
        root: Path | None = None,
        pyproject_entry_hints: set[str] | None = None,
    ) -> tuple[str, float]:
        suffix = path.suffix.lower()
        name = path.name.lower()

        if suffix == ".spec":
            return "build-script", 0.95
        if suffix == ".py" and self._is_entry_point(
            path,
            root=root or path.parent,
            pyproject_entry_hints=pyproject_entry_hints,
        ):
            return "entry-point", 0.9
        if suffix in ICON_EXTENSIONS and "icon" in name:
            return "icon", 0.95
        if suffix in ICON_EXTENSIONS:
            return "icon-candidate", 0.75
        if suffix in SPLASH_EXTENSIONS and "splash" in name:
            return "splash", 0.95
        if suffix in SPLASH_EXTENSIONS:
            return "splash-candidate", 0.7
        if suffix in DOC_EXTENSIONS:
            return "documentation", 0.9
        if suffix == ".py":
            return "source", 0.8
        return "other", 0.5

    def _is_entry_point(
        self,
        path: Path,
        root: Path | None = None,
        pyproject_entry_hints: set[str] | None = None,
    ) -> bool:
        if path.suffix.lower() != ".py":
            return False

        if path.name.lower() in {"main.py", "app.py", "run.py", "__main__.py"}:
            return True

        resolved_root = root.resolve() if root else path.parent.resolve()
        hints = pyproject_entry_hints or self._entry_points_from_pyproject(resolved_root)
        try:
            relative = path.resolve().relative_to(resolved_root).as_posix()
            if relative in hints:
                return True
        except Exception:
            pass

        return self._has_main_guard(path)

    def _entry_points_from_pyproject(self, root: Path) -> set[str]:
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return set()

        try:
            with pyproject_path.open("rb") as handle:
                data = tomllib.load(handle)
        except Exception:
            return set()

        hints: set[str] = set()
        project = data.get("project", {})
        scripts = dict(project.get("scripts", {}))
        gui_scripts = dict(project.get("gui-scripts", {}))

        tool = data.get("tool", {})
        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
        poetry_scripts = dict(poetry.get("scripts", {})) if isinstance(poetry, dict) else {}

        all_targets = list(scripts.values()) + list(gui_scripts.values()) + list(poetry_scripts.values())
        for target in all_targets:
            if not isinstance(target, str):
                continue
            module_path = target.split(":", 1)[0].strip()
            if not module_path:
                continue
            as_file = module_path.replace(".", "/") + ".py"
            as_package_main = module_path.replace(".", "/") + "/__main__.py"
            hints.add(as_file)
            hints.add(as_package_main)
        return hints

    def _has_main_guard(self, path: Path) -> bool:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return False

        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not isinstance(test, ast.Compare):
                continue
            if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
                continue
            if len(test.comparators) != 1:
                continue
            left = test.left
            right = test.comparators[0]

            left_is_name = isinstance(left, ast.Name) and left.id == "__name__"
            right_is_name = isinstance(right, ast.Name) and right.id == "__name__"
            left_is_main = isinstance(left, ast.Constant) and left.value == "__main__"
            right_is_main = isinstance(right, ast.Constant) and right.value == "__main__"

            if (left_is_name and right_is_main) or (right_is_name and left_is_main):
                return True
        return False

    def _target_folder(self, role: str) -> str:
        mapping = {
            "entry-point": "src",
            "source": "src",
            "icon": "assets/icons",
            "icon-candidate": "assets/icons",
            "splash": "assets/splash",
            "splash-candidate": "assets/splash",
            "documentation": "docs",
            "build-script": "scripts",
        }
        return mapping.get(role, "misc")