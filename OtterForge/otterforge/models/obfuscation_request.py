from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ObfuscationRequest:
    project_path: Path
    tool_name: str = "pyarmor"
    source_path: Path | None = None
    output_dir: Path | None = None
    recursive: bool = True
    raw_tool_args: list[str] = field(default_factory=list)
    environment_overrides: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False

    @staticmethod
    def _parse_raw_tool_args_string(raw_value: str) -> list[str]:
        candidate = raw_value.strip()
        if candidate in ("", "[]"):
            return []

        def parse_bracketed_tokens(value: str) -> list[str] | None:
            stripped = value.strip()
            if not (stripped.startswith("[") and stripped.endswith("]")):
                return None
            body = stripped[1:-1].strip()
            if not body:
                return []
            tokens: list[str] = []
            for token in body.split(","):
                cleaned = token.strip().strip("\"").strip("'").strip()
                cleaned = cleaned.replace('\\"', '"').replace("\\'", "'")
                if cleaned.startswith("\\") and cleaned.endswith("\\") and len(cleaned) > 1:
                    cleaned = cleaned[1:-1]
                if cleaned:
                    tokens.append(cleaned)
            return tokens

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            return [str(item) for item in parsed]

        if isinstance(parsed, str):
            nested_candidate = parsed.strip()
            try:
                nested = json.loads(nested_candidate)
            except json.JSONDecodeError:
                nested = None
            if isinstance(nested, list):
                return [str(item) for item in nested]
            bracketed_nested = parse_bracketed_tokens(nested_candidate)
            if bracketed_nested is not None:
                return bracketed_nested
            return [parsed]

        bracketed = parse_bracketed_tokens(candidate)
        if bracketed is not None:
            return bracketed

        return [candidate]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ObfuscationRequest":
        def to_path(value: Any) -> Path | None:
            if value in (None, ""):
                return None
            return Path(value)

        raw_tool_args_payload = payload.get("raw_tool_args", [])
        raw_tool_args: list[str]
        if isinstance(raw_tool_args_payload, str):
            raw_tool_args = cls._parse_raw_tool_args_string(raw_tool_args_payload)
        elif isinstance(raw_tool_args_payload, (list, tuple)):
            raw_tool_args = [str(item) for item in raw_tool_args_payload]
        elif raw_tool_args_payload in (None, ""):
            raw_tool_args = []
        else:
            raw_tool_args = [str(raw_tool_args_payload)]

        return cls(
            project_path=Path(payload.get("project_path", ".")),
            tool_name=str(payload.get("tool_name", "pyarmor")),
            source_path=to_path(payload.get("source_path")),
            output_dir=to_path(payload.get("output_dir")),
            recursive=bool(payload.get("recursive", True)),
            raw_tool_args=raw_tool_args,
            environment_overrides=dict(payload.get("environment_overrides", {})),
            dry_run=bool(payload.get("dry_run", False)),
        )
