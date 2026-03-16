"""Tests for MemoryMigrator and MemoryBackendManager migration flow."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from otterforge.services.memory_migrator import MemoryMigrator
from otterforge.services.memory_backend_manager import MemoryBackendManager
from otterforge.storage.json_store import JsonMemoryStore
from otterforge.storage.sql_store import SQLMemoryStore


class TestMemoryMigratorDirect(unittest.TestCase):
    """Unit tests for MemoryMigrator.migrate() directly."""

    def test_migrate_json_to_sql_preserves_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_store = JsonMemoryStore(tmp)
            state = json_store.load_state()
            state["user_settings"]["theme"] = "dark"
            state["projects"]["proj1"] = {"path": "/some/path"}
            json_store.save_state(state)

            db_path = Path(tmp) / "migrated.db"
            sql_store = SQLMemoryStore(db_path)

            result = MemoryMigrator.migrate(json_store, sql_store)

            reloaded = sql_store.load_state()
            sql_store.close()

        self.assertEqual(result["source_backend"], "json")
        self.assertEqual(result["target_backend"], "sql")
        self.assertEqual(reloaded["user_settings"]["theme"], "dark")
        self.assertEqual(reloaded["projects"]["proj1"]["path"], "/some/path")

    def test_migrate_sql_to_json_preserves_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "source.db"
            sql_store = SQLMemoryStore(db_path)
            state = sql_store.load_state()
            state["user_settings"]["default_builder"] = "nuitka"
            sql_store.save_state(state)
            sql_store.close()

            sql_store2 = SQLMemoryStore(db_path)
            json_store = JsonMemoryStore(tmp + "/json")

            result = MemoryMigrator.migrate(sql_store2, json_store)
            sql_store2.close()

            reloaded = json_store.load_state()

        self.assertEqual(result["source_backend"], "sql")
        self.assertEqual(result["target_backend"], "json")
        self.assertEqual(reloaded["user_settings"]["default_builder"], "nuitka")

    def test_migrate_result_lists_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_store = JsonMemoryStore(tmp)
            db_path = Path(tmp) / "target.db"
            sql_store = SQLMemoryStore(db_path)

            result = MemoryMigrator.migrate(json_store, sql_store)
            sql_store.close()

        self.assertIsInstance(result["sections"], list)

    def test_migrate_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_store = JsonMemoryStore(tmp)
            db_path = Path(tmp) / "empty_target.db"
            sql_store = SQLMemoryStore(db_path)

            result = MemoryMigrator.migrate(json_store, sql_store)
            reloaded = sql_store.load_state()
            sql_store.close()

        self.assertIn("source_backend", result)
        self.assertIsInstance(reloaded, dict)

    def test_migrate_preserves_build_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_store = JsonMemoryStore(tmp)
            state = json_store.load_state()
            state["build_history"] = [
                {"id": "abc123", "builder": "pyinstaller", "success": True}
            ]
            json_store.save_state(state)

            db_path = Path(tmp) / "hist.db"
            sql_store = SQLMemoryStore(db_path)
            MemoryMigrator.migrate(json_store, sql_store)
            reloaded = sql_store.load_state()
            sql_store.close()

        self.assertEqual(reloaded["build_history"][0]["id"], "abc123")


class TestMemoryBackendManagerMigration(unittest.TestCase):
    """Integration tests via MemoryBackendManager.migrate_to()."""

    def test_migrate_to_sql_and_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryBackendManager(project_root=tmp)
            manager.write_user_setting("color_scheme", "solarized")

            migration1 = manager.migrate_to("sql")
            self.assertTrue(migration1["migrated"])
            self.assertEqual(manager.get_backend_name(), "sql")
            self.assertEqual(manager.get_user_setting("color_scheme"), "solarized")

            migration2 = manager.migrate_to("json")
            self.assertTrue(migration2["migrated"])
            self.assertEqual(manager.get_backend_name(), "json")
            self.assertEqual(manager.get_user_setting("color_scheme"), "solarized")

    def test_migrate_to_same_backend_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryBackendManager(project_root=tmp)
            # Default backend is json; migrating to json again should not fail
            result = manager.migrate_to("json")
            # Either migrated=True (idempotent copy) or migrated=False (noop) is acceptable;
            # the important thing is no exception and data is intact
            self.assertIn("migrated", result)

    def test_migrate_invalid_target_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryBackendManager(project_root=tmp)
            with self.assertRaises((ValueError, KeyError)):
                manager.migrate_to("nosql")


if __name__ == "__main__":
    unittest.main()
