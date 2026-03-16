from __future__ import annotations

from abc import ABC, abstractmethod

from otterforge.models.obfuscation_request import ObfuscationRequest


class ObfuscatorAdapter(ABC):
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
    def validate_request(self, request: ObfuscationRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def build_command(self, request: ObfuscationRequest) -> list[str]:
        raise NotImplementedError

    def get_supported_common_options(self) -> list[str]:
        return [
            "project_path",
            "source_path",
            "output_dir",
            "recursive",
            "raw_tool_args",
            "dry_run",
        ]

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]

    def get_language_family(self) -> str:
        return "python"
