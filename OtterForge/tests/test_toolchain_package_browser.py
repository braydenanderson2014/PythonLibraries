from __future__ import annotations

import unittest
from unittest.mock import patch

from otterforge.services.toolchain_service import ToolchainService


class ToolchainPackageBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ToolchainService()

    def test_list_package_managers_returns_entries(self) -> None:
        payload = self.service.list_package_managers(os_name="windows")
        self.assertEqual(payload["os"], "windows")
        self.assertTrue(len(payload["managers"]) > 0)
        self.assertTrue(all("manager" in item for item in payload["managers"]))

    def test_search_packages_empty_query_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.service.search_packages("  ", manager="pip", os_name="windows")

    def test_install_package_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.service.install_package("   ", manager="pip", os_name="windows")

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


if __name__ == "__main__":
    unittest.main()
