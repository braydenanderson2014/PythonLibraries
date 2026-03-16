from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MCPPolicy:
    enabled: bool = False
    transport: str = "stdio"
    read_only: bool = True
    exposed_tools: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: dict[str, object]) -> "MCPPolicy":
        return cls(
            enabled=bool(config.get("enabled", False)),
            transport=str(config.get("transport", "stdio")),
            read_only=bool(config.get("read_only", True)),
            exposed_tools=list(config.get("exposed_tools", [])),
        )