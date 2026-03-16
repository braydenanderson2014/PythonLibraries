from __future__ import annotations

import unittest
from unittest.mock import patch

from otterforge.builders.registry import BuilderRegistry
from otterforge.services.toolchain_service import ToolchainService


class ToolchainPackageBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ToolchainService()

    def test_list_package_managers_returns_entries(self) -> None:
        payload = self.service.list_package_managers(os_name="windows")
        self.assertEqual(payload["os"], "windows")
        self.assertTrue(len(payload["managers"]) > 0)
        self.assertTrue(all("manager" in item for item in payload["managers"]))

    def test_list_package_managers_includes_git_and_docker_with_capabilities(self) -> None:
        payload = self.service.list_package_managers(os_name="windows")
        by_name = {str(item.get("manager")): item for item in payload.get("managers", [])}
        self.assertIn("git", by_name)
        self.assertIn("docker", by_name)
        self.assertFalse(bool(by_name["git"].get("capabilities", {}).get("supports_package_ops", True)))
        self.assertFalse(bool(by_name["docker"].get("capabilities", {}).get("supports_package_ops", True)))

    def test_search_packages_empty_query_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.service.search_packages("  ", manager="pip", os_name="windows")

    def test_install_package_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.service.install_package("   ", manager="pip", os_name="windows")

    def test_install_package_with_integration_only_manager_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.service.install_package("requests", manager="git", os_name="windows", execute=False)

    def test_install_package_plan_mode_no_execute(self) -> None:
        result = self.service.install_package(
            package_name="requests",
            manager="pip",
            os_name="windows",
            execute=False,
        )
        self.assertFalse(result["executed"])
        self.assertEqual(result["manager"], "pip")
        self.assertIn("command", result)

    def test_build_package_module_entry_includes_python_candidates(self) -> None:
        module = self.service.build_package_module_entry(
            package_name="requests",
            os_name="windows",
            ecosystem="python",
        )
        candidates = module.get("install_candidates", [])
        managers = [str(item.get("manager")) for item in candidates]
        self.assertIn("pip", managers)
        self.assertIn("uv", managers)

    def test_list_language_pack_modules_contains_candidates(self) -> None:
        modules = self.service.list_language_pack_modules(os_name="windows")
        self.assertTrue(len(modules) > 0)
        java = next((item for item in modules if item.get("pack_id") == "java"), None)
        self.assertIsNotNone(java)
        self.assertEqual(java.get("module_kind"), "language_pack")
        self.assertTrue(len(java.get("install_candidates", [])) > 0)

    def test_list_tool_modules_contains_builder_install_targets(self) -> None:
        modules = self.service.list_tool_modules(BuilderRegistry().list_builders(), os_name="windows")
        pyinstaller = next((item for item in modules if item.get("tool_id") == "pyinstaller"), None)
        self.assertIsNotNone(pyinstaller)
        self.assertEqual(pyinstaller.get("module_kind"), "builder_tool")
        self.assertEqual(pyinstaller.get("package_name"), "pyinstaller")
        self.assertTrue(len(pyinstaller.get("install_candidates", [])) > 0)

    def test_list_tool_modules_maps_cxfreeze_to_canonical_package(self) -> None:
        modules = self.service.list_tool_modules(BuilderRegistry().list_builders(), os_name="windows")
        cxfreeze = next((item for item in modules if item.get("tool_id") == "cxfreeze"), None)
        self.assertIsNotNone(cxfreeze)
        self.assertEqual(cxfreeze.get("package_name"), "cx_Freeze")

    def test_uninstall_package_plan_mode_no_execute(self) -> None:
        result = self.service.uninstall_package(
            package_name="requests",
            manager="pip",
            os_name="windows",
            execute=False,
        )
        self.assertFalse(result["executed"])
        self.assertEqual(result["manager"], "pip")
        self.assertIn("command", result)

    @patch("subprocess.run")
    def test_search_packages_executes_and_parses(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "requests (2.31.0)\n"
        run_mock.return_value.stderr = ""

        result = self.service.search_packages(
            query="requests",
            manager="pip",
            os_name="windows",
            limit=10,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["manager"], "pip")
        self.assertTrue(any(item["name"] == "requests" for item in result["results"]))

    @patch("subprocess.run")
    def test_install_package_executes(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "ok"
        run_mock.return_value.stderr = ""

        result = self.service.install_package(
            package_name="requests",
            manager="pip",
            os_name="windows",
            execute=True,
        )

        self.assertTrue(result["executed"])
        self.assertTrue(result["success"])
        self.assertEqual(result["manager"], "pip")

    @patch("subprocess.run")
    def test_uninstall_package_executes(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "removed"
        run_mock.return_value.stderr = ""

        result = self.service.uninstall_package(
            package_name="requests",
            manager="pip",
            os_name="windows",
            execute=True,
        )

        self.assertTrue(result["executed"])
        self.assertTrue(result["success"])
        self.assertEqual(result["manager"], "pip")

    def test_uv_install_plan_builds_uv_command(self) -> None:
        result = self.service.install_package(
            package_name="requests",
            manager="uv",
            os_name="windows",
            execute=False,
        )
        self.assertEqual(result["manager"], "uv")
        self.assertEqual(result["command"][:3], ["uv", "pip", "install"])

    def test_install_package_resolves_builder_alias(self) -> None:
        result = self.service.install_package(
            package_name="cxfreeze",
            manager="pip",
            os_name="windows",
            execute=False,
            ecosystem="python",
        )
        self.assertEqual(result["package"], "cx_Freeze")
        self.assertEqual(result["command"][-1], "cx_Freeze")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_install_github_repo_existing_folder_pull_policy(
        self,
        run_mock,
        which_mock,
        mkdir_mock,
        exists_mock,
    ) -> None:
        which_mock.return_value = "C:/Program Files/Git/bin/git.exe"
        exists_mock.return_value = True
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "Already up to date."
        run_mock.return_value.stderr = ""

        result = self.service.install_github_repo(
            repo_url="https://github.com/psf/requests",
            destination_root="D:/tmp/repos",
            existing_policy="pull",
            execute=True,
        )

        self.assertTrue(result["executed"])
        self.assertTrue(result["success"])
        self.assertEqual(result.get("operation"), "pull")
        self.assertEqual(result["command"][:3], ["git", "-C", result["target_dir"]])


if __name__ == "__main__":
    unittest.main()
