from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any


DEFAULT_MEMORY_STATE: dict[str, Any] = {
    "user_settings": {},
    "projects": {},
    "build_history": [],
    "profiles": {},
    "hooks": {},
    "test_configs": {},
    "signing_configs": {},
    "audit_configs": {},
    "notification_settings": {},
    "container_configs": {},
    "matrix_configs": {},
}


def create_default_memory_state() -> dict[str, Any]:
    return deepcopy(DEFAULT_MEMORY_STATE)


class MemoryStore(ABC):
    def __init__(self, store_path: str) -> None:
        self.store_path = store_path

    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def load_state(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def save_state(self, state: dict[str, Any]) -> None:
        raise NotImplementedError

    def get_section(self, section: str) -> Any:
        state = self.load_state()
        return state.get(section)

    def set_section(self, section: str, value: Any) -> None:
        state = self.load_state()
        state[section] = value
        self.save_state(state)

    def clear(self, scope: str, project_name: str | None = None) -> dict[str, Any]:
        state = self.load_state()

        if scope == "settings":
            if project_name:
                state["projects"].pop(project_name, None)
            else:
                state["projects"] = {}
        elif scope == "history":
            state["build_history"] = []
        elif scope == "profiles":
            state["profiles"] = {}
        elif scope == "all":
            state = create_default_memory_state()
        elif scope == "project":
            if not project_name:
                raise ValueError("project_name is required when clearing a project scope")
            state["projects"].pop(project_name, None)
            state["build_history"] = [
                item
                for item in state["build_history"]
                if item.get("project_name") != project_name
            ]
        else:
            raise ValueError(f"Unsupported memory clear scope: {scope}")

        self.save_state(state)
        return state

    def close(self) -> None:
        return None