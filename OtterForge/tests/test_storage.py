from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from otterforge.api.facade import OtterForgeAPI
from otterforge.services.memory_backend_manager import MemoryBackendManager
from otterforge.storage.json_store import JsonMemoryStore
from otterforge.storage.sql_store import SQLMemoryStore


class StorageTests(unittest.TestCase):
    def test_json_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JsonMemoryStore(temp_dir)
            state = store.load_state()
            state["user_settings"]["theme"] = "light"
            store.save_state(state)

            reloaded = store.load_state()
            self.assertEqual(reloaded["user_settings"]["theme"], "light")

    def test_sql_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "memory.db"
            store = SQLMemoryStore(database_path)
            state = store.load_state()
            state["projects"]["demo"] = {"path": "demo"}
            store.save_state(state)
            store.close()

            reopened = SQLMemoryStore(database_path)
            reloaded = reopened.load_state()
            reopened.close()
            self.assertEqual(reloaded["projects"]["demo"]["path"], "demo")

    def test_backend_manager_migrates_between_backends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = MemoryBackendManager(project_root=temp_dir)
            manager.write_user_setting("default_builder", "pyinstaller")

            migration_result = manager.migrate_to("sql")
            self.assertTrue(migration_result["migrated"])
            self.assertEqual(manager.get_backend_name(), "sql")
            self.assertEqual(manager.get_user_setting("default_builder"), "pyinstaller")

    def test_scan_and_export_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            (project_root / "icon.ico").write_text("stub", encoding="utf-8")
            (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            scan_result = api.scan_project(project_root)
            schema = api.export_project_schema(scan_result)

            self.assertIn(str(project_root / "main.py"), scan_result["entry_points"])
            self.assertIn(str(project_root / "icon.ico"), schema["assets"]["icons"])
            self.assertIn(str(project_root / "README.md"), schema["documentation"]["files"])
            self.assertIn("saved_to", schema)

            memory = api.load_memory()
            project_key = str(project_root.resolve())
            self.assertIn(project_key, memory["projects"])
            self.assertIn(schema["saved_to"], memory["projects"][project_key]["schema_paths"])

    def test_build_dry_run_records_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry_script = project_root / "main.py"
            entry_script.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry_script),
                    "builder_name": "pyinstaller",
                    "dry_run": True,
                    "executable_name": "DemoApp",
                }
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["final_command"][0], "pyinstaller")
            history = api.get_build_history()
            self.assertEqual(len(history), 1)

    def test_additional_builders_translate_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry_script = project_root / "main.py"
            entry_script.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            builders = {item["name"] for item in api.list_builders()}
            self.assertIn("nuitka", builders)
            self.assertIn("cxfreeze", builders)

            nuitka_result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry_script),
                    "builder_name": "nuitka",
                    "dry_run": True,
                    "mode": "onefile",
                    "executable_name": "DemoNuitka",
                }
            )
            self.assertEqual(nuitka_result["final_command"][:3], ["python", "-m", "nuitka"])

            cxfreeze_result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry_script),
                    "builder_name": "cxfreeze",
                    "dry_run": True,
                    "mode": "onedir",
                    "executable_name": "DemoCxFreeze",
                }
            )
            self.assertEqual(cxfreeze_result["final_command"][0], "cxfreeze")

    def test_new_python_builders_are_listed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            builders = {item["name"] for item in api.list_builders()}

            self.assertTrue(
                {"briefcase", "shiv", "zipapp", "py2app", "py2exe"}.issubset(builders)
            )

    def test_shiv_builder_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            api = OtterForgeAPI(project_root=project_root)

            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "builder_name": "shiv",
                    "entry_script": "demo.__main__:main",
                    "dry_run": True,
                    "executable_name": "DemoShiv",
                }
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["builder_name"], "shiv")
            self.assertEqual(result["final_command"][0], "shiv")
            self.assertIn("-e", result["final_command"])

    def test_zipapp_builder_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            api = OtterForgeAPI(project_root=project_root)

            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "builder_name": "zipapp",
                    "entry_script": "demo.__main__:main",
                    "dry_run": True,
                    "executable_name": "DemoZip",
                }
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["builder_name"], "zipapp")
            self.assertEqual(result["final_command"][1:3], ["-m", "zipapp"])

    def test_briefcase_builder_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "pyproject.toml").write_text("[tool.briefcase]\nproject_name='demo'\n", encoding="utf-8")
            api = OtterForgeAPI(project_root=project_root)

            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "builder_name": "briefcase",
                    "dry_run": True,
                }
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["builder_name"], "briefcase")
            self.assertEqual(result["final_command"][:2], ["briefcase", "build"])

    def test_package_dry_run_with_auto_packager(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "pyproject.toml").write_text(
                "[build-system]\nrequires=['setuptools']\nbuild-backend='setuptools.build_meta'\n",
                encoding="utf-8",
            )
            api = OtterForgeAPI(project_root=project_root)

            result = api.run_package(
                {
                    "project_path": str(project_root),
                    "packager_name": "auto",
                    "package_format": "wheel",
                    "dry_run": True,
                }
            )

            self.assertTrue(result["success"])
            self.assertIn(result["packager_name"], {"build", "setuptools"})
            self.assertTrue(result["final_command"])

    def test_package_list_and_inspect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            packagers = api.list_packagers()
            names = {item["name"] for item in packagers}
            self.assertTrue({"build", "setuptools", "hatch", "poetry"}.issubset(names))

            inspected = api.inspect_packager("build")
            self.assertEqual(inspected["name"], "build")
            self.assertIn("formats", inspected)

    def test_hooks_add_list_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            project_path = str(Path(temp_dir))

            added = api.add_hook(project_path, event="pre_build", command="echo hello", name="hello")
            self.assertEqual(added["event"], "pre_build")

            hooks = api.list_hooks(project_path)
            self.assertIn("pre_build", hooks)
            self.assertEqual(len(hooks["pre_build"]), 1)
            self.assertEqual(hooks["pre_build"][0]["name"], "hello")

            removed = api.remove_hook(project_path, "pre_build", 0)
            self.assertTrue(removed["removed"])

            hooks_after = api.list_hooks(project_path)
            self.assertEqual(hooks_after.get("pre_build", []), [])

    def test_version_get_and_set_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            pyproject = project_root / "pyproject.toml"
            pyproject.write_text(
                "[project]\nname='demo'\nversion='0.1.0'\n",
                encoding="utf-8",
            )
            api = OtterForgeAPI(project_root=project_root)

            version_info = api.get_version(project_root)
            self.assertEqual(version_info["pyproject_version"], "0.1.0")

            updated = api.set_version(project_root, "0.2.0", targets=["pyproject"])
            self.assertIn("pyproject", updated)

            version_info_after = api.get_version(project_root)
            self.assertEqual(version_info_after["pyproject_version"], "0.2.0")

    def test_obfuscators_list_and_inspect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            obfuscators = api.list_obfuscators()
            names = {item["name"] for item in obfuscators}

            self.assertTrue(
                {
                    "pyarmor",
                    "pyminifier",
                    "nuitka",
                    "cythonize",
                    "javascript-obfuscator",
                    "garble",
                    "native-strip",
                    "proguard",
                    "obfuscar",
                }.issubset(names)
            )

            by_name = {item["name"]: item for item in obfuscators}
            self.assertEqual(by_name["pyarmor"]["language_family"], "python")
            self.assertEqual(by_name["javascript-obfuscator"]["language_family"], "javascript")
            self.assertEqual(by_name["garble"]["language_family"], "go")
            self.assertEqual(by_name["native-strip"]["language_family"], "native")
            self.assertEqual(by_name["proguard"]["language_family"], "java")
            self.assertEqual(by_name["obfuscar"]["language_family"], "dotnet")

            inspected = api.inspect_obfuscator("pyarmor")
            self.assertEqual(inspected["name"], "pyarmor")
            self.assertEqual(inspected["category"], "obfuscator")
            self.assertEqual(inspected["language_family"], "python")
            self.assertIn("project_path", inspected["supported_common_options"])

    def test_obfuscation_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "main.py"
            source_path.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "pyarmor",
                    "source_path": str(source_path),
                    "output_dir": str(project_root / "dist-obf"),
                    "dry_run": True,
                    "recursive": True,
                    "raw_tool_args": ["--private"],
                }
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["final_command"][:2], ["pyarmor", "gen"])
            self.assertIn("--private", result["final_command"])
            self.assertEqual(result["final_command"][-1], str(source_path))
            self.assertEqual(
                result["environment_snapshot"]["cwd"],
                str(source_path.parent.resolve()),
            )

    def test_pyminifier_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "main.py"
            source_path.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "pyminifier",
                    "source_path": str(source_path),
                    "output_dir": str(project_root / "dist-obf"),
                    "dry_run": True,
                }
            )

            self.assertEqual(result["final_command"][0], "pyminifier")
            self.assertIn("--obfuscate", result["final_command"])
            self.assertIn("-o", result["final_command"])

    def test_nuitka_obfuscator_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "main.py"
            source_path.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "nuitka",
                    "source_path": str(source_path),
                    "dry_run": True,
                }
            )

            command = result["final_command"]
            if command[0] == "nuitka":
                prefix = command[:1]
            else:
                prefix = command[:3]
                self.assertEqual(prefix, [sys.executable, "-m", "nuitka"])
            self.assertTrue(prefix)
            self.assertIn("--standalone", command)
            self.assertIn("--remove-output", command)

    def test_javascript_obfuscator_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "app.js"
            source_path.write_text("console.log('hello');\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "javascript-obfuscator",
                    "source_path": str(source_path),
                    "output_dir": str(project_root / "dist-obf"),
                    "dry_run": True,
                }
            )

            self.assertEqual(result["final_command"][0], "javascript-obfuscator")
            self.assertIn("--output", result["final_command"])

    def test_native_strip_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "app.bin"
            source_path.write_text("binary", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "native-strip",
                    "source_path": str(source_path),
                    "dry_run": True,
                    "raw_tool_args": ["--strip-debug"],
                }
            )

            self.assertEqual(result["final_command"][0], "strip")
            self.assertIn("--strip-debug", result["final_command"])

    def test_proguard_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "app.jar"
            source_path.write_text("jar-stub", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "proguard",
                    "source_path": str(source_path),
                    "output_dir": str(project_root / "dist-obf"),
                    "dry_run": True,
                }
            )

            self.assertEqual(result["final_command"][0], "proguard")
            self.assertIn("-injars", result["final_command"])
            self.assertIn("-outjars", result["final_command"])

    def test_obfuscar_dry_run_returns_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "obfuscar.xml"
            source_path.write_text("<Obfuscator></Obfuscator>", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "tool_name": "obfuscar",
                    "source_path": str(source_path),
                    "dry_run": True,
                }
            )

            self.assertIn(result["final_command"][0], {"obfuscar.console", "obfuscar"})
            self.assertEqual(result["final_command"][1], str(source_path))

    def test_obfuscation_request_parses_raw_tool_args_string_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "main.py"
            source_path.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "source_path": str(source_path),
                    "dry_run": True,
                    "raw_tool_args": '["--private"]',
                }
            )

            self.assertIn("--private", result["final_command"])
            self.assertNotIn("[", result["final_command"])

    def test_obfuscation_request_parses_bracketed_raw_tool_args_string(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_path = project_root / "main.py"
            source_path.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_obfuscation(
                {
                    "project_path": str(project_root),
                    "source_path": str(source_path),
                    "dry_run": True,
                    "raw_tool_args": "[--private]",
                }
            )

            self.assertIn("--private", result["final_command"])
            self.assertNotIn("[--private]", result["final_command"])

    def test_profile_crud(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            created = api.create_profile(
                "desktop",
                settings={"builder": "pyinstaller", "mode": "onefile"},
                description="Desktop release profile",
            )
            self.assertEqual(created["name"], "desktop")

            profiles = api.list_profiles()
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0]["name"], "desktop")

            loaded = api.show_profile("desktop")
            self.assertEqual(loaded["settings"]["mode"], "onefile")

    def test_project_organizer_copy_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            source_main = project_root / "main.py"
            source_readme = project_root / "README.md"
            source_main.write_text("print('hello')\n", encoding="utf-8")
            source_readme.write_text("# Demo\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            plan = api.create_organization_plan(project_root, mode="copy")
            plan_path = project_root / "organize_plan.json"
            api.save_organization_plan(plan, plan_path)

            apply_result = api.apply_organization_plan(plan_path)
            manifest_path = Path(apply_result["manifest_path"])
            self.assertTrue(manifest_path.exists())

            copied_main = project_root / "src" / "main.py"
            copied_readme = project_root / "docs" / "README.md"
            self.assertTrue(copied_main.exists())
            self.assertTrue(copied_readme.exists())
            self.assertTrue(source_main.exists())

            rollback_result = api.rollback_organization(manifest_path)
            self.assertTrue(any(item["status"] == "rolled-back" for item in rollback_result["operations"]))
            self.assertFalse(copied_main.exists())
            self.assertFalse(copied_readme.exists())
            self.assertTrue(source_main.exists())

    def test_mcp_tool_execution_requires_enabled_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            with self.assertRaises(RuntimeError):
                api.execute_mcp_tool("list_builders")

    def test_mcp_tool_execution_enforces_policy_and_executes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            api.start_mcp_server()

            read_result = api.execute_mcp_tool("list_builders")
            self.assertEqual(read_result["tool_id"], "list_builders")
            self.assertIsInstance(read_result["result"], list)

            api.set_mcp_tool_visibility("set_memory_backend", True)
            with self.assertRaises(PermissionError):
                api.execute_mcp_tool("set_memory_backend", {"backend": "sql"})

            api.set_mcp_read_only(False)

            write_result = api.execute_mcp_tool("set_memory_backend", {"backend": "sql"})
            self.assertEqual(write_result["tool_id"], "set_memory_backend")
            self.assertEqual(write_result["result"]["backend"], "sql")

    def test_mcp_default_read_tools_include_profiles_organizer_and_obfuscators(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            api.start_mcp_server()
            tool_ids = {item["tool_id"] for item in api.list_mcp_tools()}
            self.assertIn("list_profiles", tool_ids)
            self.assertIn("show_profile", tool_ids)
            self.assertIn("create_organization_plan", tool_ids)
            self.assertIn("list_obfuscators", tool_ids)
            self.assertIn("inspect_obfuscator", tool_ids)

    def test_toolchain_doctor_reports_install_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            doctor = api.doctor_toolchain()
            self.assertIn("summary", doctor)
            self.assertIn("missing", doctor)

            if doctor["missing"]:
                first_missing = doctor["missing"][0]
                self.assertIn("install", first_missing)
                self.assertIn("managers", first_missing["install"])

    def test_language_pack_list_contains_expected_packs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            packs = api.list_language_packs()
            self.assertGreaterEqual(packs["count"], 2)
            pack_ids = {item["pack_id"] for item in packs["packs"]}
            self.assertIn("c_cpp", pack_ids)
            self.assertIn("java", pack_ids)

    def test_language_pack_install_plan_returns_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            plan = api.install_language_pack(
                "c_cpp",
                manager="winget",
                os_name="windows",
                execute=False,
            )
            self.assertFalse(plan["executed"])
            self.assertEqual(plan["pack_id"], "c_cpp")
            self.assertEqual(plan["manager"], "winget")
            self.assertGreaterEqual(len(plan["commands"]), 1)

    def test_language_pack_install_unknown_pack_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            with self.assertRaises(KeyError):
                api.install_language_pack("unknown-pack", execute=False)

    def test_manifest_refresh_and_toggle_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            api = OtterForgeAPI(project_root=root)

            manifest = api.refresh_manifest()
            self.assertIn("entries", manifest)
            self.assertGreaterEqual(len(manifest["entries"]), 1)

            capability_id = str(manifest["entries"][0]["id"])
            disabled = api.disable_manifest_capability(capability_id)
            self.assertFalse(disabled["enabled"])

            enabled = api.enable_manifest_capability(capability_id)
            self.assertTrue(enabled["enabled"])

            manifest_path = root / ".otterforge" / "otterforge.manifest.json"
            self.assertTrue(manifest_path.exists())

    def test_modules_list_reads_pyproject_and_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                """
[project]
name = "demo"
version = "0.0.1"
dependencies = ["requests>=2", "pydantic>=2"]

[project.optional-dependencies]
dev = ["pytest>=8"]
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "requirements.txt").write_text("rich>=13\n# comment\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=root)
            modules = api.list_modules(root)
            self.assertIn("requests>=2", modules["all_modules"])
            self.assertIn("pytest>=8", modules["all_modules"])
            self.assertIn("rich>=13", modules["all_modules"])

    def test_compiler_config_crud(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)

            saved = api.set_compiler_config(
                "release",
                language="c",
                settings={
                    "compiler": "gcc",
                    "standard": "c17",
                    "optimization": "O2",
                    "debug_symbols": False,
                    "include_paths": ["/usr/local/include"],
                    "libraries": ["pthread"],
                },
                description="Release build for C",
            )
            self.assertEqual(saved["name"], "release")
            self.assertEqual(saved["language"], "c")
            self.assertEqual(saved["settings"]["standard"], "c17")
            self.assertIn("/usr/local/include", saved["settings"]["include_paths"])

            all_configs = api.list_compiler_configs()
            self.assertEqual(all_configs["count"], 1)

            by_lang = api.list_compiler_configs(language="c")
            self.assertEqual(by_lang["count"], 1)

            shown = api.show_compiler_config("release", language="c")
            self.assertEqual(shown["settings"]["compiler"], "gcc")

            deleted = api.delete_compiler_config("release", language="c")
            self.assertEqual(deleted["name"], "release")

            empty = api.list_compiler_configs(language="c")
            self.assertEqual(empty["count"], 0)

    def test_auto_builder_selection_by_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry_c = project_root / "main.c"
            entry_c.write_text("int main(){return 0;}", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry_c),
                    "builder_name": "auto",
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            self.assertIn(result["final_command"][0], {"gcc", "clang", "cc"})

    def test_auto_builder_selection_explicit_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry = project_root / "main.c"
            entry.write_text("int main(){return 0;}", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry),
                    "builder_name": "auto",
                    "language": "c",
                    "executable_name": "demo",
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            self.assertIn(result["final_command"][0], {"gcc", "clang", "cc"})
            self.assertIn("-o", result["final_command"])

    def test_build_with_named_compiler_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry = project_root / "main.cpp"
            entry.write_text("int main(){return 0;}", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            api.set_compiler_config(
                "debug-cpp",
                language="cpp",
                settings={"standard": "c++17", "debug_symbols": True},
            )
            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry),
                    "builder_name": "auto",
                    "compiler_config_name": "debug-cpp",
                    "executable_name": "demo",
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            command = result["final_command"]
            self.assertIn("-std=c++17", command)
            self.assertIn("-g", command)

    def test_compiler_config_missing_name_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            with self.assertRaises(KeyError):
                api.show_compiler_config("nonexistent", language="c")

    def test_builders_list_includes_non_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            builders = {item["name"] for item in api.list_builders()}
            self.assertIn("c", builders)
            self.assertIn("cpp", builders)
            self.assertIn("rust", builders)
            self.assertIn("go", builders)
            self.assertIn("pyinstaller", builders)

    # ------------------------------------------------------------------
    # Installer tier
    # ------------------------------------------------------------------

    def test_installer_list_returns_all_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            installers = api.list_installers()
            names = {item["name"] for item in installers}
            self.assertGreaterEqual(len(installers), 5)
            self.assertTrue({"inno", "nsis", "wix", "appimage", "pkgbuild"}.issubset(names))

    def test_installer_inspect_returns_info(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            info = api.inspect_installer("inno")
            self.assertEqual(info["name"], "inno")
            self.assertIn("available", info)

    def test_installer_inspect_unknown_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            result = api.inspect_installer("nonexistent_installer")
            self.assertIn("error", result)

    def test_installer_dry_run_inno(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            iss_file = Path(temp_dir) / "setup.iss"
            iss_file.write_text("; stub iss\n", encoding="utf-8")
            api = OtterForgeAPI(project_root=temp_dir)
            result = api.run_installer(
                {
                    "project_path": temp_dir,
                    "installer_name": "inno",
                    "source_artifacts": [str(iss_file)],
                    "application_name": "MyApp",
                    "version": "1.0.0",
                    "output_dir": str(Path(temp_dir) / "installer_out"),
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            self.assertIn("iscc", result["final_command"])
            self.assertIn(str(iss_file), result["final_command"])

    def test_installer_dry_run_nsis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            nsi_file = Path(temp_dir) / "setup.nsi"
            nsi_file.write_text("; stub nsi\n", encoding="utf-8")
            api = OtterForgeAPI(project_root=temp_dir)
            result = api.run_installer(
                {
                    "project_path": temp_dir,
                    "installer_name": "nsis",
                    "source_artifacts": [str(nsi_file)],
                    "application_name": "MyApp",
                    "output_dir": str(Path(temp_dir) / "installer_out"),
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            self.assertIn("makensis", result["final_command"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "AppImage is Linux-only")
    def test_installer_dry_run_appimage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "AppDir"
            app_dir.mkdir()
            api = OtterForgeAPI(project_root=temp_dir)
            result = api.run_installer(
                {
                    "project_path": temp_dir,
                    "installer_name": "appimage",
                    "source_artifacts": [str(app_dir)],
                    "application_name": "MyApp",
                    "output_dir": str(Path(temp_dir) / "installer_out"),
                    "dry_run": True,
                }
            )
            self.assertTrue(result["success"])
            self.assertIn("appimagetool", result["final_command"])

    def test_installer_validation_missing_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            result = api.run_installer(
                {
                    "project_path": temp_dir,
                    "installer_name": "inno",
                    "source_artifacts": [],
                    "dry_run": True,
                }
            )
            # Validation should fail (no script) before subprocess
            self.assertFalse(result["success"])
            self.assertIn("source_artifacts", result["stderr"])

    # ------------------------------------------------------------------
    # Plugin system
    # ------------------------------------------------------------------

    def test_plugins_list_empty_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            plugins = api.list_plugins()
            self.assertIsInstance(plugins, list)

    def test_plugin_install_and_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a minimal plugin file
            plugin_src = Path(temp_dir) / "myplugin.py"
            plugin_src.write_text(
                "BUILDER_ADAPTERS = []\nPACKAGER_ADAPTERS = []\nINSTALLER_ADAPTERS = []\n",
                encoding="utf-8",
            )
            api = OtterForgeAPI(project_root=temp_dir)
            # Override plugin_dir so install goes to a temp location
            api.plugin_loader.plugin_dir = Path(temp_dir) / "plugins"

            result = api.install_plugin(str(plugin_src))
            self.assertTrue(result["success"], result.get("error"))
            self.assertEqual(result["name"], "myplugin")

            plugins = api.list_plugins()
            self.assertEqual(len(plugins), 1)
            self.assertEqual(plugins[0]["name"], "myplugin")

            removed = api.remove_plugin("myplugin")
            self.assertTrue(removed["success"])
            self.assertEqual(len(api.list_plugins()), 0)

    def test_plugin_discover_lists_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "plugins"
            plugin_dir.mkdir()
            (plugin_dir / "myplugin.py").write_text("BUILDER_ADAPTERS=[]\n", encoding="utf-8")
            api = OtterForgeAPI(project_root=temp_dir)
            api.plugin_loader.plugin_dir = plugin_dir

            discovered = api.discover_plugins()
            names = [d["name"] for d in discovered]
            self.assertIn("myplugin", names)

    # ------------------------------------------------------------------
    # Checksum & release manifest
    # ------------------------------------------------------------------

    def test_generate_checksums_creates_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "myapp.exe"
            artifact.write_bytes(b"fake binary content")

            api = OtterForgeAPI(project_root=temp_dir)
            result = api.generate_checksums(
                [str(artifact)], output_dir=temp_dir, metadata={"version": "1.0"}
            )

            self.assertIn("checksums_file", result)
            self.assertIn("manifest_file", result)
            self.assertTrue(Path(result["checksums_file"]).exists())
            self.assertTrue(Path(result["manifest_file"]).exists())

            checksums_text = Path(result["checksums_file"]).read_text()
            self.assertIn("myapp.exe", checksums_text)
            self.assertRegex(checksums_text, r"[0-9a-f]{64}")

    def test_checksums_content_is_correct(self) -> None:
        import hashlib

        with tempfile.TemporaryDirectory() as temp_dir:
            content = b"hello otterforge"
            artifact = Path(temp_dir) / "artifact.bin"
            artifact.write_bytes(content)

            api = OtterForgeAPI(project_root=temp_dir)
            result = api.generate_checksums([str(artifact)], output_dir=temp_dir)

            expected_hash = hashlib.sha256(content).hexdigest()
            checksums_text = Path(result["checksums_file"]).read_text()
            self.assertIn(expected_hash, checksums_text)

    # ------------------------------------------------------------------
    # Size analyzer
    # ------------------------------------------------------------------

    def test_size_analyser_reports_totals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir) / "dist"
            dist_dir.mkdir()
            (dist_dir / "app.exe").write_bytes(b"x" * 1024)
            (dist_dir / "readme.txt").write_bytes(b"y" * 512)
            sub = dist_dir / "lib"
            sub.mkdir()
            (sub / "module.py").write_bytes(b"z" * 256)

            api = OtterForgeAPI(project_root=temp_dir)
            report = api.analyse_size(str(dist_dir))

            self.assertEqual(report["total_files"], 3)
            self.assertEqual(report["total_bytes"], 1024 + 512 + 256)
            self.assertGreater(len(report["top_files"]), 0)
            top_names = [f["path"] for f in report["top_files"]]
            self.assertIn("app.exe", top_names)

    def test_size_analyser_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            report = api.analyse_size(str(Path(temp_dir) / "nonexistent"))
            self.assertIn("error", report)


    def test_test_runner_config_and_build_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            entry_script = project_root / "main.py"
            entry_script.write_text("print('hello')\n", encoding="utf-8")

            api = OtterForgeAPI(project_root=project_root)
            fail_cmd = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
            cfg = api.set_test_config(project_root, command=fail_cmd, gate_enabled=True)
            self.assertTrue(cfg["gate_enabled"])

            loaded = api.get_test_config(project_root)
            self.assertEqual(loaded["command"], fail_cmd)

            result = api.run_build(
                {
                    "project_path": str(project_root),
                    "entry_script": str(entry_script),
                    "builder_name": "pyinstaller",
                    "dry_run": True,
                }
            )
            self.assertFalse(result["success"])
            self.assertIn("test gate failed", result["stderr"].lower())

    def test_notification_config_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = OtterForgeAPI(project_root=temp_dir)
            updated = api.set_notification_config(enabled=True, webhook_url="https://example.invalid")
            self.assertTrue(updated["enabled"])

            loaded = api.get_notification_config()
            self.assertTrue(loaded["enabled"])
            self.assertEqual(loaded["webhook_url"], "https://example.invalid")

    def test_container_and_signing_config_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            api = OtterForgeAPI(project_root=project_root)

            container_cfg = api.set_container_config(project_root, image="python:3.12-slim")
            self.assertEqual(container_cfg["image"], "python:3.12-slim")
            self.assertEqual(api.get_container_config(project_root)["image"], "python:3.12-slim")

            signing_cfg = api.set_signing_config(
                project_root,
                tool="gpg",
                key_id="ABC123",
            )
            self.assertEqual(signing_cfg["tool"], "gpg")
            loaded_signing = api.get_signing_config(project_root)
            self.assertEqual(loaded_signing["tool"], "gpg")
            self.assertEqual(loaded_signing["key_id"], "ABC123")

    def test_matrix_and_ci_generation_from_stored_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            api = OtterForgeAPI(project_root=project_root)

            entries = [
                {
                    "profile_name": "linux-release",
                    "builder_name": "pyinstaller",
                    "platform": "linux",
                    "dry_run": True,
                }
            ]
            defined = api.define_matrix(project_root, entries)
            self.assertEqual(defined["entries"], 1)

            workflow_path = project_root / "workflow.yml"
            generated = api.generate_ci_workflow(project_root, profiles=[], output_path=workflow_path)
            self.assertEqual(generated["jobs"], 1)
            self.assertTrue(workflow_path.exists())


if __name__ == "__main__":
    unittest.main()