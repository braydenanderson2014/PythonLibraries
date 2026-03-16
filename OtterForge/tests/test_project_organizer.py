"""Tests for ProjectOrganizer service."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile

from otterforge.services.project_organizer import ProjectOrganizer
from otterforge.services.project_scanner import ProjectScanner


def _make_scan(tmp_path: Path, file_names: list[str]) -> dict:
    """Create files and return a minimal scan result dict."""
    for name in file_names:
        (tmp_path / name).write_text(f"# {name}", encoding="utf-8")
    scanner = ProjectScanner()
    return scanner.discover(str(tmp_path))


class TestProjectOrganizer(unittest.TestCase):

    # ------------------------------------------------------------------
    # Plan generation — filesystem must NOT be mutated
    # ------------------------------------------------------------------

    def test_create_plan_returns_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py", "README.md"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan)
        self.assertIn("plan_id", plan)
        self.assertIn("actions", plan)
        self.assertIn("mode", plan)
        self.assertIn("root_path", plan)

    def test_create_plan_does_not_mutate_filesystem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.py").write_text("pass", encoding="utf-8")
            scanner = ProjectScanner()
            scan = scanner.discover(str(root))
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            # Capture after organizer init — __init__ creates the manifests dir
            before = set(root.iterdir())
            organizer.create_plan(root, scan)
            after = set(root.iterdir())
        self.assertEqual(before, after)

    def test_plan_mode_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan, mode="copy")
        self.assertEqual(plan["mode"], "copy")

    def test_plan_mode_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan, mode="move")
        self.assertEqual(plan["mode"], "move")

    def test_plan_invalid_mode_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            with self.assertRaises(ValueError):
                organizer.create_plan(root, scan, mode="invalid")

    def test_plan_actions_have_source_target_mode_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan)
        for action in plan["actions"]:
            self.assertIn("source", action)
            self.assertIn("target", action)
            self.assertIn("mode", action)
            self.assertIn("role", action)

    def test_file_already_in_target_location_not_in_plan(self) -> None:
        """File already at its suggested target folder should produce no action.

        main.py is an entry-point → suggested_target_folder = 'src'.
        If it already lives at <root>/src/main.py the organizer must skip it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("pass", encoding="utf-8")
            # Scan from root so the scanner sees the full tree
            scanner = ProjectScanner()
            scan = scanner.discover(str(root))
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            # Root for the plan is also root — so target = root/src/main.py = source
            plan = organizer.create_plan(root, scan)
        # main.py is already at root/src/main.py → no action expected
        moved_names = [Path(a["source"]).name for a in plan["actions"]]
        self.assertEqual(moved_names.count("main.py"), 0)

    # ------------------------------------------------------------------
    # Save / load plan
    # ------------------------------------------------------------------

    def test_save_and_load_plan_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan = _make_scan(root, ["main.py", "README.md"])
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan)
            plan_path = root / "plan.json"
            saved = organizer.save_plan(plan, plan_path)
            loaded = organizer.load_plan(saved)
        self.assertEqual(plan["plan_id"], loaded["plan_id"])
        self.assertEqual(len(plan["actions"]), len(loaded["actions"]))

    # ------------------------------------------------------------------
    # Apply plan
    # ------------------------------------------------------------------

    def test_apply_copy_plan_creates_target_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig = root / "main.py"
            orig.write_text("pass", encoding="utf-8")
            scan = _make_scan(root, [])
            scan["files"] = [
                {
                    "path": str(orig),
                    "name": "main.py",
                    "extension": ".py",
                    "role": "entry-point",
                    "confidence": 0.9,
                    "suggested_target_folder": "src",
                }
            ]
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan, mode="copy")
            result = organizer.apply_plan(plan)
            applied = [op for op in result["operations"] if op["status"] == "applied"]
            self.assertTrue(len(applied) > 0)
            # Original still exists (copy mode)
            self.assertTrue(orig.exists())
            # Target file created
            self.assertTrue(Path(applied[0]["target"]).exists())

    def test_apply_skips_when_target_exists_no_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig = root / "main.py"
            orig.write_text("pass", encoding="utf-8")
            # Pre-create the target
            target_dir = root / "src"
            target_dir.mkdir()
            (target_dir / "main.py").write_text("existing", encoding="utf-8")

            action = {
                "source": str(orig),
                "target": str(target_dir / "main.py"),
                "mode": "copy",
                "role": "entry-point",
            }
            plan = {"plan_id": "test", "actions": [action], "root_path": str(root), "mode": "copy"}
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            result = organizer.apply_plan(plan, force=False)

        skipped = [op for op in result["operations"] if op["status"] == "skipped-target-exists"]
        self.assertTrue(len(skipped) > 0)

    def test_apply_writes_manifest_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig = root / "main.py"
            orig.write_text("pass", encoding="utf-8")
            scan = _make_scan(root, [])
            scan["files"] = [
                {
                    "path": str(orig),
                    "name": "main.py",
                    "extension": ".py",
                    "role": "entry-point",
                    "confidence": 0.9,
                    "suggested_target_folder": "src",
                }
            ]
            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            plan = organizer.create_plan(root, scan, mode="copy")
            result = organizer.apply_plan(plan)
            manifest_path = Path(result["manifest_path"])
            self.assertTrue(manifest_path.exists())

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def test_rollback_reverses_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig = root / "main.py"
            orig.write_text("pass", encoding="utf-8")
            target_dir = root / "src"
            target_dir.mkdir()
            target = target_dir / "main.py"

            action = {
                "source": str(orig),
                "target": str(target),
                "mode": "move",
                "role": "entry-point",
            }
            plan = {"plan_id": "test", "actions": [action], "root_path": str(root), "mode": "move"}

            organizer = ProjectOrganizer(manifest_dir=root / "manifests")
            apply_result = organizer.apply_plan(plan)
            manifest_path = apply_result["manifest_path"]

            # After move: original gone, target exists
            self.assertFalse(orig.exists())
            self.assertTrue(target.exists())

            # Rollback
            organizer.rollback(manifest_path)

            # After rollback: original restored, target gone
            self.assertTrue(orig.exists())
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
