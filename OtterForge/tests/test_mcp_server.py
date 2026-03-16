"""Tests for MCPServer, MCPPolicy, and MCPToolRegistry."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from otterforge.mcp.policy import MCPPolicy
from otterforge.mcp.server import MCPServer
from otterforge.mcp.tool_registry import DEFAULT_MCP_TOOLS, MCPToolRegistry
from otterforge.services.memory_backend_manager import MemoryBackendManager


def _server_in_tmp(tmp: str) -> MCPServer:
    manager = MemoryBackendManager(project_root=tmp)
    return MCPServer(backend_manager=manager)


class TestMCPPolicy(unittest.TestCase):

    def test_default_policy_disabled_and_read_only(self) -> None:
        policy = MCPPolicy()
        self.assertFalse(policy.enabled)
        self.assertTrue(policy.read_only)
        self.assertEqual(policy.transport, "stdio")

    def test_from_config_maps_fields(self) -> None:
        config = {
            "enabled": True,
            "transport": "http",
            "read_only": False,
            "exposed_tools": ["list_builders", "scan_project"],
        }
        policy = MCPPolicy.from_config(config)
        self.assertTrue(policy.enabled)
        self.assertEqual(policy.transport, "http")
        self.assertFalse(policy.read_only)
        self.assertIn("list_builders", policy.exposed_tools)

    def test_from_config_defaults_for_missing_keys(self) -> None:
        policy = MCPPolicy.from_config({})
        self.assertFalse(policy.enabled)
        self.assertTrue(policy.read_only)
        self.assertEqual(policy.exposed_tools, [])


class TestMCPToolRegistry(unittest.TestCase):

    def test_read_only_policy_excludes_mutating_tools(self) -> None:
        policy = MCPPolicy(enabled=True, read_only=True, exposed_tools=[t.tool_id for t in DEFAULT_MCP_TOOLS])
        registry = MCPToolRegistry(policy)
        tools = registry.list_tools()
        for tool in tools:
            self.assertFalse(
                tool.mutating,
                msg=f"Mutating tool '{tool.tool_id}' must not appear in read-only mode",
            )

    def test_non_read_only_policy_includes_mutating_tools(self) -> None:
        policy = MCPPolicy(enabled=True, read_only=False, exposed_tools=[t.tool_id for t in DEFAULT_MCP_TOOLS])
        registry = MCPToolRegistry(policy)
        tools = registry.list_tools()
        mutating = [t for t in tools if t.mutating]
        self.assertTrue(len(mutating) > 0)

    def test_allowlist_restricts_tools(self) -> None:
        policy = MCPPolicy(enabled=True, read_only=False, exposed_tools=["list_builders"])
        registry = MCPToolRegistry(policy)
        tools = registry.list_tools()
        ids = [t.tool_id for t in tools]
        self.assertIn("list_builders", ids)
        self.assertNotIn("run_build", ids)

    def test_empty_allowlist_returns_no_tools(self) -> None:
        policy = MCPPolicy(enabled=True, read_only=True, exposed_tools=[])
        registry = MCPToolRegistry(policy)
        self.assertEqual(registry.list_tools(), [])


class TestMCPServerStatus(unittest.TestCase):

    def test_status_reflects_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            status = server.status()
        self.assertFalse(status["enabled"])

    def test_status_has_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            status = server.status()
        for key in ("enabled", "transport", "read_only", "exposed_tool_count", "exposed_tools"):
            self.assertIn(key, status)

    def test_start_enables_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            status = server.start(transport="stdio")
        self.assertTrue(status["enabled"])
        self.assertEqual(status["transport"], "stdio")

    def test_stop_disables_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            status = server.stop()
        self.assertFalse(status["enabled"])

    def test_set_read_only_updates_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            status = server.set_read_only(False)
        self.assertFalse(status["read_only"])


class TestMCPServerListTools(unittest.TestCase):

    def test_list_tools_returns_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            tools = server.list_tools()
        self.assertIsInstance(tools, list)

    def test_list_tools_entries_have_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            tools = server.list_tools()
        for tool in tools:
            self.assertIn("tool_id", tool)
            self.assertIn("description", tool)
            self.assertIn("mutating", tool)


class TestMCPServerToolVisibility(unittest.TestCase):

    def test_set_tool_visible_adds_to_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            status = server.set_tool_visibility("list_builders", True)
        self.assertIn("list_builders", status["exposed_tools"])

    def test_set_tool_hidden_removes_from_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.set_tool_visibility("list_builders", True)
            status = server.set_tool_visibility("list_builders", False)
        self.assertNotIn("list_builders", status["exposed_tools"])


class TestMCPServerExecuteTool(unittest.TestCase):

    def test_execute_tool_when_server_disabled_raises_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            # server is disabled by default
            with self.assertRaises(RuntimeError):
                server.execute_tool("list_builders", {})

    def test_execute_tool_not_exposed_raises_permission_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            # Do not expose the tool
            server.set_tool_visibility("run_build", False)
            with self.assertRaises(PermissionError):
                server.execute_tool("run_build", {})

    def test_execute_mutating_tool_blocked_in_read_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            server.set_read_only(True)
            server.set_tool_visibility("run_build", True)
            # Must register a handler so we reach the policy check
            server.register_tool_handler("run_build", lambda args: {})
            with self.assertRaises(PermissionError):
                server.execute_tool("run_build", {})

    def test_execute_read_only_tool_succeeds_in_read_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            server.set_read_only(True)
            server.set_tool_visibility("list_builders", True)
            server.register_tool_handler("list_builders", lambda args: {"builders": []})
            result = server.execute_tool("list_builders", {})
        self.assertEqual(result, {"tool_id": "list_builders", "result": {"builders": []}})

    def test_execute_unknown_tool_raises_key_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            server.set_tool_visibility("ghost_tool", True)
            with self.assertRaises((KeyError, PermissionError)):
                server.execute_tool("ghost_tool", {})

    def test_execute_tool_without_handler_raises_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = _server_in_tmp(tmp)
            server.start()
            server.set_read_only(False)
            server.set_tool_visibility("list_builders", True)
            # No handler registered for list_builders
            with self.assertRaises(NotImplementedError):
                server.execute_tool("list_builders", {})


if __name__ == "__main__":
    unittest.main()
