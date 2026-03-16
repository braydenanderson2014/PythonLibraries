"""Packager adapter base class."""
from __future__ import annotations

from abc import ABC, abstractmethod

from otterforge.models.package_request import PackageRequest


class PackagerAdapter(ABC):
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
    def get_supported_formats(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def package_command(self, request: PackageRequest) -> list[str]:
        raise NotImplementedError

    def validate_request(self, request: PackageRequest) -> None:
        pass

    def get_supported_platforms(self) -> list[str]:
        return ["windows", "linux", "macos"]
