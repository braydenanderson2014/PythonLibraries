from __future__ import annotations

from otterforge.obfuscators.base import ObfuscatorAdapter
from otterforge.obfuscators.cythonize import CythonizeAdapter
from otterforge.obfuscators.garble import GarbleAdapter
from otterforge.obfuscators.javascript_obfuscator import JavaScriptObfuscatorAdapter
from otterforge.obfuscators.native_strip import NativeStripAdapter
from otterforge.obfuscators.nuitka import NuitkaObfuscatorAdapter
from otterforge.obfuscators.obfuscar import ObfuscarAdapter
from otterforge.obfuscators.proguard import ProGuardAdapter
from otterforge.obfuscators.pyminifier import PyMinifierAdapter
from otterforge.obfuscators.pyarmor import PyArmorAdapter


class ObfuscatorRegistry:
    def __init__(self) -> None:
        self._obfuscators: dict[str, ObfuscatorAdapter] = {}
        self.register(PyArmorAdapter())
        self.register(PyMinifierAdapter())
        self.register(NuitkaObfuscatorAdapter())
        self.register(CythonizeAdapter())
        self.register(JavaScriptObfuscatorAdapter())
        self.register(GarbleAdapter())
        self.register(NativeStripAdapter())
        self.register(ProGuardAdapter())
        self.register(ObfuscarAdapter())

    def register(self, adapter: ObfuscatorAdapter) -> None:
        self._obfuscators[adapter.name] = adapter

    def get(self, name: str) -> ObfuscatorAdapter:
        if name not in self._obfuscators:
            raise KeyError(f"Unknown obfuscator: {name}")
        return self._obfuscators[name]

    def list_obfuscators(self) -> list[dict[str, object]]:
        return [
            {
                "name": adapter.name,
                "language_family": adapter.get_language_family(),
                "available": adapter.is_available(),
                "version": adapter.get_version(),
                "platforms": adapter.get_supported_platforms(),
            }
            for adapter in self._obfuscators.values()
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
            "category": "obfuscator",
        }
