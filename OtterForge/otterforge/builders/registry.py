from __future__ import annotations

from otterforge.builders.base import ToolAdapter
from otterforge.builders.briefcase import BriefcaseAdapter
from otterforge.builders.c_builder import CBuilderAdapter
from otterforge.builders.cpp_builder import CppBuilderAdapter
from otterforge.builders.cxfreeze import CxFreezeAdapter
from otterforge.builders.go_builder import GoBuilderAdapter
from otterforge.builders.nuitka import NuitkaAdapter
from otterforge.builders.py2app import Py2AppAdapter
from otterforge.builders.py2exe import Py2ExeAdapter
from otterforge.builders.pyinstaller import PyInstallerAdapter
from otterforge.builders.rust_builder import RustBuilderAdapter
from otterforge.builders.shiv import ShivAdapter
from otterforge.builders.zipapp_builder import ZipAppAdapter


class BuilderRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, ToolAdapter] = {}
        self.register(PyInstallerAdapter())
        self.register(NuitkaAdapter())
        self.register(CxFreezeAdapter())
        self.register(BriefcaseAdapter())
        self.register(ShivAdapter())
        self.register(ZipAppAdapter())
        self.register(Py2AppAdapter())
        self.register(Py2ExeAdapter())
        self.register(CBuilderAdapter())
        self.register(CppBuilderAdapter())
        self.register(RustBuilderAdapter())
        self.register(GoBuilderAdapter())

    def register(self, adapter: ToolAdapter) -> None:
        self._builders[adapter.name] = adapter

    def get(self, name: str) -> ToolAdapter:
        if name not in self._builders:
            raise KeyError(f"Unknown builder: {name}")
        return self._builders[name]

    def list_builders(self) -> list[dict[str, object]]:
        return [
            {
                "name": adapter.name,
                "language_family": adapter.get_language_family(),
                "available": adapter.is_available(),
                "version": adapter.get_version(),
                "platforms": adapter.get_supported_platforms(),
            }
            for adapter in self._builders.values()
        ]

    def inspect(self, name: str) -> dict[str, object]:
        adapter = self.get(name)
        return {
            "name": adapter.name,
            "language_family": adapter.get_language_family(),
            "available": adapter.is_available(),
            "version": adapter.get_version(),
            "supported_common_options": adapter.get_supported_common_options(),
            "platforms": adapter.get_supported_platforms(),
            "output_types": adapter.get_output_types(),
            "category": adapter.get_tool_category(),
        }