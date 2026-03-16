from __future__ import annotations

from typing import Any

from otterforge.models.profile import Profile


class ProfileService:
    def create_profile(
        self,
        state: dict[str, Any],
        name: str,
        settings: dict[str, Any],
        description: str = "",
    ) -> dict[str, Any]:
        profile = Profile(name=name, description=description, settings=settings)
        state.setdefault("profiles", {})[name] = {
            "name": profile.name,
            "description": profile.description,
            "settings": profile.settings,
        }
        return state

    def list_profiles(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        profiles = state.get("profiles", {})
        return [profiles[key] for key in sorted(profiles)]

    def get_profile(self, state: dict[str, Any], name: str) -> dict[str, Any]:
        profiles = state.get("profiles", {})
        if name not in profiles:
            raise KeyError(f"Profile '{name}' not found")
        return profiles[name]
