from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from otterforge.models.build_request import BuildRequest


class ToolAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_version(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_supported_common_options(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def validate_request(self, build_request: BuildRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def build_command(self, build_request: BuildRequest) -> list[str]:
        raise NotImplementedError

    def execute(self, build_request: BuildRequest) -> list[str]:
        self.validate_request(build_request)
        return self.build_command(build_request)

    def summarize_result(self, process_result: Any) -> dict[str, Any]:
        return {"returncode": getattr(process_result, "returncode", None)}

    def get_tool_category(self) -> str:
        return "builder"

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]

    def get_output_types(self) -> list[str]:
        return ["executable"]

    def get_language_family(self) -> str:
        return "python"