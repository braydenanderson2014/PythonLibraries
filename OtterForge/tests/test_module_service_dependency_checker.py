from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from otterforge.api.facade import OtterForgeAPI


class ModuleServiceDependencyCheckerTests(unittest.TestCase):
    def test_list_modules_includes_dependency_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "main.py").write_text("import requests\nimport json\n", encoding="utf-8")
            (root / "requirements.txt").write_text("requests>=2\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=root)
            modules = api.list_modules(root)

            self.assertIn("dependency_inventory", modules)
            self.assertIn("missing_dependencies", modules)
            self.assertIn("imports", modules)
            self.assertTrue(any(item.get("name") == "requests" for item in modules["dependency_inventory"]))

    def test_dependency_inventory_marks_installed_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "requirements.txt").write_text("totally_fake_dep_xyz>=1\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=root)
            modules = api.list_modules(root)

            dep = next(
                item for item in modules["dependency_inventory"]
                if item.get("name") == "totally_fake_dep_xyz"
            )
            self.assertFalse(dep["installed"])
            self.assertIn("totally_fake_dep_xyz", modules["missing_dependencies"])

    def test_import_scanning_collects_non_stdlib_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text(
                "import requests\nfrom pydantic import BaseModel\nimport os\n",
                encoding="utf-8",
            )

            api = OtterForgeAPI(project_root=root)
            modules = api.list_modules(root)

            inferred = set(modules["imports"]["inferred_modules"])
            self.assertIn("requests", inferred)
            self.assertIn("pydantic", inferred)
            self.assertNotIn("os", inferred)


if __name__ == "__main__":
    unittest.main()
