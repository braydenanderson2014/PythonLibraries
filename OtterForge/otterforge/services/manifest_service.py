from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ManifestService:
    def __init__(self, manifest_path: Path | str) -> None:
        self.manifest_path = Path(manifest_path)

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {
                "manifest_version": 1,
                "generated_at": None,
                "entries": [],
            }

        with self.manifest_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def refresh_manifest(
        self,
        builders: list[dict[str, Any]],
        obfuscators: list[dict[str, Any]],
        language_packs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        existing = self.load_manifest()
        enabled_by_id = {
            str(entry.get("id")): bool(entry.get("enabled", False))
            for entry in existing.get("entries", [])
            if isinstance(entry, dict) and entry.get("id")
        }

        timestamp = datetime.now(UTC).isoformat()
        entries: list[dict[str, Any]] = []

        for builder in builders:
            tool_id = str(builder["name"])
            available = bool(builder.get("available", False))
            entries.append(
                self._entry(
                    capability_id=f"builder.{tool_id}",
                    category="builder",
                    display_name=tool_id,
                    description=f"Builder adapter for {tool_id}",
                    available=available,
                    enabled=enabled_by_id.get(f"builder.{tool_id}", available),
                    requires=[tool_id],
                    missing=[] if available else [tool_id],
                    platform_support=list(builder.get("platforms", [])) or ["windows", "linux", "macos"],
                    adapter_module=None,
                    version_detected=builder.get("version"),
                    last_checked=timestamp,
                )
            )

        for obfuscator in obfuscators:
            tool_id = str(obfuscator["name"])
            available = bool(obfuscator.get("available", False))
            language = str(obfuscator.get("language_family", "unknown"))
            entries.append(
                self._entry(
                    capability_id=f"obfuscator.{tool_id}",
                    category="obfuscator",
                    display_name=tool_id,
                    description=f"{language} obfuscation adapter",
                    available=available,
                    enabled=enabled_by_id.get(f"obfuscator.{tool_id}", available),
                    requires=[tool_id],
                    missing=[] if available else [tool_id],
                    platform_support=list(obfuscator.get("platforms", [])) or ["windows", "linux", "macos"],
                    adapter_module=None,
                    version_detected=obfuscator.get("version"),
                    last_checked=timestamp,
                )
            )

        for pack in language_packs:
            pack_id = str(pack["pack_id"])
            managers = sorted(
                {
                    manager
                    for manager_list in pack.get("managers", {}).values()
                    for manager in manager_list
                }
            )
            entries.append(
                self._entry(
                    capability_id=f"language.{pack_id}",
                    category="language",
                    display_name=str(pack.get("name", pack_id)),
                    description=str(pack.get("description", "Language pack")),
                    available=True,
                    enabled=enabled_by_id.get(f"language.{pack_id}", True),
                    requires=managers,
                    missing=[],
                    platform_support=sorted(pack.get("managers", {}).keys()),
                    adapter_module=None,
                    version_detected=None,
                    last_checked=timestamp,
                )
            )

        manifest = {
            "manifest_version": 1,
            "generated_at": timestamp,
            "entries": sorted(entries, key=lambda item: str(item["id"])),
        }
        self.save_manifest(manifest)
        return manifest

    def set_enabled(self, capability_id: str, enabled: bool) -> dict[str, Any]:
        manifest = self.load_manifest()
        entries = manifest.get("entries", [])

        for entry in entries:
            if str(entry.get("id")) != capability_id:
                continue
            entry["enabled"] = enabled
            self.save_manifest(manifest)
            return entry

        raise KeyError(f"Unknown capability id: {capability_id}")

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)

    def _entry(
        self,
        capability_id: str,
        category: str,
        display_name: str,
        description: str,
        available: bool,
        enabled: bool,
        requires: list[str],
        missing: list[str],
        platform_support: list[str],
        adapter_module: str | None,
        version_detected: str | None,
        last_checked: str,
    ) -> dict[str, Any]:
        return {
            "id": capability_id,
            "category": category,
            "display_name": display_name,
            "description": description,
            "available": available,
            "enabled": enabled,
            "requires": requires,
            "missing": missing,
            "platform_support": platform_support,
            "adapter_module": adapter_module,
            "version_detected": version_detected,
            "last_checked": last_checked,
        }
