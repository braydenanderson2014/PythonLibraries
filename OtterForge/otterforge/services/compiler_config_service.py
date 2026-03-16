from __future__ import annotations

from typing import Any


class CompilerConfigService:
    def save_config(
        self,
        state: dict[str, Any],
        name: str,
        language: str,
        settings: dict[str, Any],
        description: str = "",
    ) -> dict[str, Any]:
        normalized_language = self._normalize_language(language)
        if not name.strip():
            raise ValueError("Config name cannot be empty")
        if not isinstance(settings, dict):
            raise TypeError("settings must be a JSON object")

        user_settings = state.setdefault("user_settings", {})
        by_language = user_settings.setdefault("compiler_configs", {})
        by_name = by_language.setdefault(normalized_language, {})
        by_name[name] = {
            "name": name,
            "language": normalized_language,
            "description": description,
            "settings": self._normalize_settings(settings),
        }
        return state

    def list_configs(
        self,
        state: dict[str, Any],
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        by_language = state.get("user_settings", {}).get("compiler_configs", {})
        if language is not None:
            normalized_language = self._normalize_language(language)
            names = by_language.get(normalized_language, {})
            return [names[key] for key in sorted(names)]

        results: list[dict[str, Any]] = []
        for language_key in sorted(by_language):
            names = by_language.get(language_key, {})
            for name in sorted(names):
                results.append(names[name])
        return results

    def get_config(
        self,
        state: dict[str, Any],
        name: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        if language is not None:
            normalized_language = self._normalize_language(language)
            names = state.get("user_settings", {}).get("compiler_configs", {}).get(normalized_language, {})
            if name not in names:
                raise KeyError(f"Compiler config '{name}' not found for language '{normalized_language}'")
            return names[name]

        matches: list[dict[str, Any]] = []
        by_language = state.get("user_settings", {}).get("compiler_configs", {})
        for names in by_language.values():
            if name in names:
                matches.append(names[name])

        if not matches:
            raise KeyError(f"Compiler config '{name}' not found")
        if len(matches) > 1:
            raise ValueError(
                f"Compiler config '{name}' exists in multiple languages; specify language explicitly"
            )
        return matches[0]

    def delete_config(
        self,
        state: dict[str, Any],
        name: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        user_settings = state.setdefault("user_settings", {})
        by_language = user_settings.setdefault("compiler_configs", {})

        if language is not None:
            normalized_language = self._normalize_language(language)
            names = by_language.get(normalized_language, {})
            if name not in names:
                raise KeyError(f"Compiler config '{name}' not found for language '{normalized_language}'")
            return names.pop(name)

        found: list[tuple[str, dict[str, Any]]] = []
        for language_key, names in by_language.items():
            if name in names:
                found.append((language_key, names[name]))

        if not found:
            raise KeyError(f"Compiler config '{name}' not found")
        if len(found) > 1:
            raise ValueError(
                f"Compiler config '{name}' exists in multiple languages; specify language explicitly"
            )

        language_key, config = found[0]
        by_language.get(language_key, {}).pop(name, None)
        return config

    def resolve_settings(
        self,
        state: dict[str, Any],
        name: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        config = self.get_config(state, name, language=language)
        return dict(config.get("settings", {}))

    def _normalize_language(self, language: str) -> str:
        value = language.strip().lower()
        if value in {"", "auto"}:
            raise ValueError("language is required for compiler configs")
        if value in {"c++", "cplusplus"}:
            return "cpp"
        return value

    def _normalize_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(settings)

        for key in ("include_paths", "library_paths", "libraries", "raw_builder_args"):
            value = normalized.get(key)
            if value is None:
                continue
            if isinstance(value, list):
                normalized[key] = [str(item) for item in value if item not in (None, "")]
            else:
                normalized[key] = [str(value)]

        if "debug_symbols" in normalized:
            normalized["debug_symbols"] = bool(normalized["debug_symbols"])

        return normalized
