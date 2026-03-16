from __future__ import annotations

from collections.abc import Callable
from typing import Any

from otterforge.mcp.policy import MCPPolicy
from otterforge.mcp.tool_registry import DEFAULT_MCP_TOOLS, MCPToolRegistry
from otterforge.services.memory_backend_manager import MemoryBackendManager


class MCPServer:
    def __init__(self, backend_manager: MemoryBackendManager | None = None) -> None:
        self.backend_manager = backend_manager or MemoryBackendManager()
        self._tool_handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_tool_handler(self, tool_id: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._tool_handlers[tool_id] = handler

    def _load_policy(self) -> MCPPolicy:
        config = self.backend_manager.load_runtime_config()
        return MCPPolicy.from_config(config.get("mcp", {}))

    def status(self) -> dict[str, Any]:
        policy = self._load_policy()
        tools = MCPToolRegistry(policy).list_tools()
        return {
            "enabled": policy.enabled,
            "transport": policy.transport,
            "read_only": policy.read_only,
            "exposed_tool_count": len(tools),
            "exposed_tools": [tool.tool_id for tool in tools],
        }

    def start(self, transport: str = "stdio") -> dict[str, Any]:
        config = self.backend_manager.load_runtime_config()
        config["mcp"]["enabled"] = True
        config["mcp"]["transport"] = transport
        self.backend_manager.save_runtime_config(config)
        return self.status()

    def stop(self) -> dict[str, Any]:
        config = self.backend_manager.load_runtime_config()
        config["mcp"]["enabled"] = False
        self.backend_manager.save_runtime_config(config)
        return self.status()

    def set_read_only(self, enabled: bool) -> dict[str, Any]:
        config = self.backend_manager.load_runtime_config()
        config["mcp"]["read_only"] = bool(enabled)
        self.backend_manager.save_runtime_config(config)
        return self.status()

    def list_tools(self) -> list[dict[str, Any]]:
        policy = self._load_policy()
        registry = MCPToolRegistry(policy)
        return [
            {
                "tool_id": descriptor.tool_id,
                "description": descriptor.description,
                "mutating": descriptor.mutating,
            }
            for descriptor in registry.list_tools()
        ]

    def set_tool_visibility(self, tool_id: str, enabled: bool) -> dict[str, Any]:
        config = self.backend_manager.load_runtime_config()
        exposed_tools = set(config["mcp"].get("exposed_tools", []))
        if enabled:
            exposed_tools.add(tool_id)
        else:
            exposed_tools.discard(tool_id)
        config["mcp"]["exposed_tools"] = sorted(exposed_tools)
        self.backend_manager.save_runtime_config(config)
        return self.status()

    def execute_tool(self, tool_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = self._load_policy()
        if not policy.enabled:
            raise RuntimeError("MCP server is disabled. Start it before executing tools.")

        if tool_id not in policy.exposed_tools:
            raise PermissionError(f"MCP tool '{tool_id}' is not exposed.")

        descriptor_by_id = {descriptor.tool_id: descriptor for descriptor in DEFAULT_MCP_TOOLS}
        descriptor = descriptor_by_id.get(tool_id)
        if descriptor is None:
            raise KeyError(f"MCP tool '{tool_id}' is not recognized.")

        if policy.read_only and descriptor.mutating:
            raise PermissionError(f"MCP tool '{tool_id}' is blocked by read_only policy.")

        allowed_tools = {descriptor.tool_id for descriptor in MCPToolRegistry(policy).list_tools()}
        if tool_id not in allowed_tools:
            raise PermissionError(f"MCP tool '{tool_id}' is blocked by policy.")

        handler = self._tool_handlers.get(tool_id)
        if handler is None:
            raise NotImplementedError(f"No MCP handler is registered for tool '{tool_id}'.")

        payload = arguments or {}
        if not isinstance(payload, dict):
            raise TypeError("MCP tool arguments must be a JSON object.")

        return {
            "tool_id": tool_id,
            "result": handler(payload),
        }