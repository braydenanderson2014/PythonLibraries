"""Tests for PluginLoader service."""
from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
import tempfile

from otterforge.plugins.loader import PluginLoader


_VALID_PLUGIN = textwrap.dedent("""\
    BUILDER_ADAPTERS = []
    PACKAGER_ADAPTERS = []
    INSTALLER_ADAPTERS = []

    def hello():
        return "plugin_loaded"
""")

_BROKEN_PLUGIN = textwrap.dedent("""\
    raise RuntimeError("intentional load failure")
""")

_BUILDER_PLUGIN = textwrap.dedent("""\
    class _FakeBuilder:
        name = "fake_builder"

    BUILDER_ADAPTERS = [_FakeBuilder()]
    PACKAGER_ADAPTERS = []
    INSTALLER_ADAPTERS = []
""")


class TestPluginLoaderDiscover(unittest.TestCase):

    def test_discover_empty_dir_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = PluginLoader(plugin_dir=tmp)
            results = loader.discover()
        self.assertEqual(results, [])

    def test_discover_nonexistent_dir_returns_empty_list(self) -> None:
        loader = PluginLoader(plugin_dir="/nonexistent/plugins/dir")
        results = loader.discover()
        self.assertEqual(results, [])

    def test_discover_returns_plugin_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "myplugin.py"
            plugin_file.write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            results = loader.discover()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "myplugin")
        self.assertIn("path", results[0])
        self.assertIn("loaded", results[0])

    def test_discover_multiple_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "alpha.py").write_text(_VALID_PLUGIN, encoding="utf-8")
            (Path(tmp) / "beta.py").write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            results = loader.discover()
        names = {r["name"] for r in results}
        self.assertIn("alpha", names)
        self.assertIn("beta", names)


class TestPluginLoaderLoad(unittest.TestCase):

    def test_load_valid_plugin_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "myplugin.py"
            plugin_file.write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.load("myplugin")
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "myplugin")

    def test_load_nonexistent_plugin_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.load("does_not_exist")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_load_broken_plugin_returns_failure_not_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "broken.py"
            plugin_file.write_text(_BROKEN_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.load("broken")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("intentional", result["error"])

    def test_load_plugin_registers_builders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "builderplugin.py"
            plugin_file.write_text(_BUILDER_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.load("builderplugin")
        self.assertTrue(result["success"])
        self.assertIn("fake_builder", result["builders"])

    def test_load_path_explicit_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "explicit.py"
            plugin_file.write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.load_path(str(plugin_file))
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "explicit")

    def test_loaded_plugin_appears_in_discover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "myplugin.py"
            plugin_file.write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            loader.load("myplugin")
            results = loader.discover()
        loaded_entry = next((r for r in results if r["name"] == "myplugin"), None)
        self.assertIsNotNone(loaded_entry)
        self.assertTrue(loaded_entry["loaded"])


class TestPluginLoaderInstall(unittest.TestCase):

    def test_install_copies_and_loads_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir:
            with tempfile.TemporaryDirectory() as plugin_dir:
                source = Path(src_dir) / "external.py"
                source.write_text(_VALID_PLUGIN, encoding="utf-8")
                loader = PluginLoader(plugin_dir=plugin_dir)
                result = loader.install(str(source))
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "external")

    def test_install_nonexistent_source_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.install("/nonexistent/plugin.py")
        self.assertFalse(result["success"])


class TestPluginLoaderUnload(unittest.TestCase):

    def test_unload_loaded_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_file = Path(tmp) / "myplugin.py"
            plugin_file.write_text(_VALID_PLUGIN, encoding="utf-8")
            loader = PluginLoader(plugin_dir=tmp)
            loader.load("myplugin")
            result = loader.unload("myplugin")
        self.assertTrue(result.get("success", False))

    def test_unload_unknown_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = PluginLoader(plugin_dir=tmp)
            result = loader.unload("ghost")
        self.assertFalse(result.get("success", True))


if __name__ == "__main__":
    unittest.main()
