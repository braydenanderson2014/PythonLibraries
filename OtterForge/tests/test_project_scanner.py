"""Tests for ProjectScanner service."""
from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from otterforge.services.project_scanner import ProjectScanner, IGNORED_PARTS


class TestProjectScanner(unittest.TestCase):

    def setUp(self) -> None:
        self.scanner = ProjectScanner()

    # ------------------------------------------------------------------
    # Basic discovery
    # ------------------------------------------------------------------

    def test_discover_returns_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "app.py").write_text("print('hi')", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertIn("path", result)
        self.assertIn("scope", result)
        self.assertIn("entry_points", result)
        self.assertIn("files", result)
        self.assertIn("spec_files", result)

    def test_discover_nonexistent_path_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.scanner.discover("/nonexistent/path/that/surely/does/not/exist")

    def test_default_scope_is_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scanner.discover(tmp)
        self.assertEqual(result["scope"], "projects")

    def test_scope_passthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scanner.discover(tmp, scope="files")
        self.assertEqual(result["scope"], "files")

    # ------------------------------------------------------------------
    # Entry point detection
    # ------------------------------------------------------------------

    def test_main_py_detected_as_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertTrue(any("main.py" in ep for ep in result["entry_points"]))

    def test_app_py_detected_as_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "app.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertTrue(any("app.py" in ep for ep in result["entry_points"]))

    def test_run_py_detected_as_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "run.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertTrue(any("run.py" in ep for ep in result["entry_points"]))

    def test_dunder_main_py_detected_as_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "__main__.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertTrue(any("__main__.py" in ep for ep in result["entry_points"]))

    def test_other_py_not_an_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "utils.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertEqual(result["entry_points"], [])

    def test_main_guard_marks_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "cli.py").write_text(
                "def run():\n    return 0\n\nif __name__ == '__main__':\n    run()\n",
                encoding="utf-8",
            )
            result = self.scanner.discover(tmp)
        self.assertTrue(any("cli.py" in ep for ep in result["entry_points"]))

    def test_pyproject_scripts_mark_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                """
[project]
name = "demo"
version = "0.1.0"

[project.scripts]
demo = "demo.cli:main"
""".strip() + "\n",
                encoding="utf-8",
            )
            demo_dir = root / "demo"
            demo_dir.mkdir()
            (demo_dir / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertTrue(any("demo/cli.py" in ep.replace("\\", "/") for ep in result["entry_points"]))

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def test_icon_file_classified_as_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "icon.ico").write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        self.assertTrue(any(r["name"] == "icon.ico" and "icon" in r["role"] for r in records))

    def test_png_named_icon_gets_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "icon.png").write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        icon_records = [r for r in records if r["name"] == "icon.png"]
        self.assertTrue(len(icon_records) > 0)
        self.assertEqual(icon_records[0]["role"], "icon")
        self.assertAlmostEqual(icon_records[0]["confidence"], 0.95)

    def test_splash_gif_classified(self) -> None:
        # .gif is ONLY in SPLASH_EXTENSIONS (not ICON_EXTENSIONS), so it correctly
        # gets a splash role when the filename contains "splash".
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "splash.gif").write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        splash = [r for r in records if r["name"] == "splash.gif"]
        self.assertTrue(len(splash) > 0)
        self.assertEqual(splash[0]["role"], "splash")

    def test_png_classified_as_icon_candidate(self) -> None:
        # .png is in ICON_EXTENSIONS, so a generic .png without "icon" in the
        # name gets "icon-candidate", not "splash-candidate".
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "background.png").write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        rec = [r for r in records if r["name"] == "background.png"]
        self.assertTrue(len(rec) > 0)
        self.assertEqual(rec[0]["role"], "icon-candidate")

    def test_readme_md_classified_as_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# Docs", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        doc = [r for r in records if r["name"] == "README.md"]
        self.assertTrue(len(doc) > 0)
        self.assertEqual(doc[0]["role"], "documentation")

    def test_txt_rst_docx_pdf_classified_as_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("CHANGES.txt", "guide.rst", "manual.docx", "ref.pdf"):
                (root / name).write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        roles = {r["name"]: r["role"] for r in result["files"]}
        for name in ("CHANGES.txt", "guide.rst", "manual.docx", "ref.pdf"):
            self.assertEqual(roles.get(name), "documentation", f"{name} should be documentation")

    def test_spec_file_classified_as_build_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "MyApp.spec").write_text("# pyinstaller spec", encoding="utf-8")
            result = self.scanner.discover(tmp)
        records = result["files"]
        spec = [r for r in records if r["name"] == "MyApp.spec"]
        self.assertTrue(len(spec) > 0)
        self.assertEqual(spec[0]["role"], "build-script")
        self.assertTrue(any("MyApp.spec" in s for s in result["spec_files"]))

    # ------------------------------------------------------------------
    # Ignored paths
    # ------------------------------------------------------------------

    def test_pycache_dir_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pycache = Path(tmp) / "__pycache__"
            pycache.mkdir()
            (pycache / "app.cpython-312.pyc").write_bytes(b"")
            result = self.scanner.discover(tmp)
        self.assertEqual(result["files"], [])

    def test_venv_dir_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = Path(tmp) / ".venv"
            venv_dir.mkdir()
            (venv_dir / "python.exe").write_bytes(b"")
            result = self.scanner.discover(tmp)
        self.assertEqual(result["files"], [])

    def test_git_dir_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            git_dir = Path(tmp) / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("[core]", encoding="utf-8")
            result = self.scanner.discover(tmp)
        self.assertEqual(result["files"], [])

    def test_pyc_files_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "compiled.pyc").write_bytes(b"")
            result = self.scanner.discover(tmp)
        self.assertEqual(result["files"], [])

    # ------------------------------------------------------------------
    # include_extensions filter
    # ------------------------------------------------------------------

    def test_include_extensions_filters_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("pass", encoding="utf-8")
            (root / "README.md").write_text("# doc", encoding="utf-8")
            result = self.scanner.discover(tmp, include_extensions=[".py"])
        names = {r["name"] for r in result["files"]}
        self.assertIn("app.py", names)
        self.assertNotIn("README.md", names)

    def test_include_extensions_without_dot_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "app.py").write_text("pass", encoding="utf-8")
            (Path(tmp) / "helper.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp, include_extensions=["py"])
        self.assertEqual(len(result["files"]), 2)

    # ------------------------------------------------------------------
    # Target folder mapping
    # ------------------------------------------------------------------

    def test_suggested_target_folder_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        for record in result["files"]:
            self.assertIn("suggested_target_folder", record)
            self.assertIsInstance(record["suggested_target_folder"], str)

    def test_entry_point_maps_to_src(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("pass", encoding="utf-8")
            result = self.scanner.discover(tmp)
        ep_records = [r for r in result["files"] if r["name"] == "main.py"]
        self.assertEqual(ep_records[0]["suggested_target_folder"], "src")

    def test_icon_maps_to_assets_icons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "icon.ico").write_text("stub", encoding="utf-8")
            result = self.scanner.discover(tmp)
        icon_records = [r for r in result["files"] if r["name"] == "icon.ico"]
        self.assertEqual(icon_records[0]["suggested_target_folder"], "assets/icons")

    def test_doc_maps_to_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# doc", encoding="utf-8")
            result = self.scanner.discover(tmp)
        doc_records = [r for r in result["files"] if r["name"] == "README.md"]
        self.assertEqual(doc_records[0]["suggested_target_folder"], "docs")


if __name__ == "__main__":
    unittest.main()
