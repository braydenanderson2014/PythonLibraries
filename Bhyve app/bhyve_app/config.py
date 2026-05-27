from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENV_VAR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


DEFAULT_CONFIG_TEMPLATE: dict[str, Any] = {
    "bhyve": {
        "email": "you@example.com",
        "password_env": "BHYVE_PASSWORD",
        "poll_interval_seconds": 300,
        "request_timeout_seconds": 30,
    },
    "weather": {
        "provider": "open_meteo",
        "latitude": 40.7608,
        "longitude": -111.891,
        "temperature_unit": "fahrenheit",
    },
    "controller": {
        "schedule_guard_minutes": 30,
        "default_cooldown_minutes": 120,
        "default_max_runs_per_day": 3,
        "automatic_weather_delay_enabled": False,
        "automatic_weather_delay_probability_threshold": 60,
        "automatic_weather_delay_lookahead_hours": 12,
        "manual_weather_delay_until": None,
        "state_file": ".bhyve_state.json",
    },
    "rules": [
        {
            "name": "Front Lawn Heat Boost",
            "device_id": "replace-with-device-id",
            "station": 1,
            "start_above": 88,
            "stop_below": 78,
            "manual_run_minutes": 10,
            "cooldown_minutes": 180,
            "max_runs_per_day": 2,
            "allowed_hours_local": [10, 19],
            "enabled": True,
        }
    ],
}


@dataclass(slots=True)
class BhyveSettings:
    email: str | None
    password: str | None
    api_key: str | None
    credential_mode: str
    poll_interval_seconds: int
    request_timeout_seconds: int


@dataclass(slots=True)
class WeatherSettings:
    provider: str
    latitude: float
    longitude: float
    temperature_unit: str


@dataclass(slots=True)
class ControllerSettings:
    schedule_guard_minutes: int
    default_cooldown_minutes: int
    default_max_runs_per_day: int
    automatic_weather_delay_enabled: bool
    automatic_weather_delay_probability_threshold: int
    automatic_weather_delay_lookahead_hours: int
    manual_weather_delay_until: datetime | None
    state_file: Path


@dataclass(slots=True)
class TemperatureRule:
    name: str
    device_id: str
    station: int
    start_above: float
    stop_below: float
    manual_run_minutes: float
    enabled: bool
    max_runs_per_day: int | None
    cooldown_minutes: int | None
    allowed_hours_local: tuple[int, int] | None


@dataclass(slots=True)
class AppConfig:
    path: Path
    bhyve: BhyveSettings
    weather: WeatherSettings
    controller: ControllerSettings
    rules: list[TemperatureRule]


def looks_like_env_var_name(value: object) -> bool:
    return isinstance(value, str) and bool(ENV_VAR_NAME_RE.fullmatch(value.strip()))


def default_config_template() -> dict[str, Any]:
    return deepcopy(DEFAULT_CONFIG_TEMPLATE)


def load_raw_config(config_path: Path) -> dict[str, Any]:
    resolved_path = config_path.expanduser().resolve()
    if not resolved_path.exists():
        return default_config_template()

    data = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object")
    return data


def save_raw_config(config_path: Path, data: dict[str, Any]) -> Path:
    resolved_path = config_path.expanduser().resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return resolved_path


def _require_positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _require_positive_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise ValueError(f"{name} must be a positive number")
    return float(value)


def _require_percentage(value: object, name: str) -> int:
    if not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError(f"{name} must be an integer from 0-100")
    return value


def _parse_optional_datetime(value: object, name: str) -> datetime | None:
    if value in {None, ""}:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO datetime string or null")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string or null") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_allowed_hours(value: object) -> tuple[int, int] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("allowed_hours_local must be a two-item list")
    start_hour, end_hour = value
    if not all(isinstance(hour, int) and 0 <= hour <= 23 for hour in value):
        raise ValueError("allowed_hours_local values must be integers from 0-23")
    if start_hour == end_hour:
        raise ValueError("allowed_hours_local start and end cannot match")
    return (start_hour, end_hour)


def _resolve_secret(raw: dict, literal_key: str, env_key: str) -> str:
    literal = raw.get(literal_key)
    if literal:
        return str(literal)
    env_name = raw.get(env_key)
    if env_name:
        env_name = str(env_name).strip()
        value = os.environ.get(env_name)
        if value:
            return value
        if not looks_like_env_var_name(env_name):
            return env_name
        raise ValueError(f"Environment variable {env_name} is not set")
    raise ValueError(f"Missing {literal_key} or {env_key} in bhyve config")


def _resolve_optional_secret(raw: dict, literal_key: str, env_key: str) -> str | None:
    literal = raw.get(literal_key)
    if literal:
        return str(literal)
    env_name = raw.get(env_key)
    if env_name:
        env_name = str(env_name).strip()
        value = os.environ.get(env_name)
        if value:
            return value
        if not looks_like_env_var_name(env_name):
            return env_name
        raise ValueError(f"Environment variable {env_name} is not set")
    return None


def parse_app_config(data: dict[str, Any], config_path: Path) -> AppConfig:
    config_path = config_path.expanduser().resolve()
    bhyve_data = data.get("bhyve") or {}
    weather_data = data.get("weather") or {}
    controller_data = data.get("controller") or {}
    rules_data = data.get("rules") or []

    if not isinstance(rules_data, list):
        raise ValueError("rules must be a list")

    api_key = _resolve_optional_secret(bhyve_data, "api_key", "api_key_env")
    credential_mode = str(bhyve_data.get("credential_mode") or "").strip().lower()
    if api_key:
        email = str(bhyve_data.get("email") or "").strip() or None
        password = None
        resolved_credential_mode = "token"
    else:
        email = _resolve_secret(bhyve_data, "email", "email_env")
        password = _resolve_secret(bhyve_data, "password", "password_env")
        if credential_mode in {"password", "env"}:
            resolved_credential_mode = credential_mode
        else:
            resolved_credential_mode = "password"

    bhyve = BhyveSettings(
        email=email,
        password=password,
        api_key=api_key,
        credential_mode=resolved_credential_mode,
        poll_interval_seconds=_require_positive_int(
            bhyve_data.get("poll_interval_seconds", 300),
            "bhyve.poll_interval_seconds",
        ),
        request_timeout_seconds=_require_positive_int(
            bhyve_data.get("request_timeout_seconds", 30),
            "bhyve.request_timeout_seconds",
        ),
    )

    temperature_unit = str(
        weather_data.get("temperature_unit", "fahrenheit")
    ).lower()
    if temperature_unit not in {"fahrenheit", "celsius"}:
        raise ValueError("weather.temperature_unit must be 'fahrenheit' or 'celsius'")

    provider = str(weather_data.get("provider", "open_meteo")).lower()
    if provider != "open_meteo":
        raise ValueError("Only the 'open_meteo' weather provider is supported")

    weather = WeatherSettings(
        provider=provider,
        latitude=float(weather_data["latitude"]),
        longitude=float(weather_data["longitude"]),
        temperature_unit=temperature_unit,
    )

    state_path = Path(str(controller_data.get("state_file", ".bhyve_state.json")))
    if not state_path.is_absolute():
        state_path = config_path.parent / state_path

    controller = ControllerSettings(
        schedule_guard_minutes=_require_positive_int(
            controller_data.get("schedule_guard_minutes", 30),
            "controller.schedule_guard_minutes",
        ),
        default_cooldown_minutes=_require_positive_int(
            controller_data.get("default_cooldown_minutes", 120),
            "controller.default_cooldown_minutes",
        ),
        default_max_runs_per_day=_require_positive_int(
            controller_data.get("default_max_runs_per_day", 3),
            "controller.default_max_runs_per_day",
        ),
        automatic_weather_delay_enabled=bool(
            controller_data.get("automatic_weather_delay_enabled", False)
        ),
        automatic_weather_delay_probability_threshold=_require_percentage(
            controller_data.get("automatic_weather_delay_probability_threshold", 60),
            "controller.automatic_weather_delay_probability_threshold",
        ),
        automatic_weather_delay_lookahead_hours=_require_positive_int(
            controller_data.get("automatic_weather_delay_lookahead_hours", 12),
            "controller.automatic_weather_delay_lookahead_hours",
        ),
        manual_weather_delay_until=_parse_optional_datetime(
            controller_data.get("manual_weather_delay_until"),
            "controller.manual_weather_delay_until",
        ),
        state_file=state_path,
    )

    rules: list[TemperatureRule] = []
    for index, raw_rule in enumerate(rules_data, start=1):
        name = str(raw_rule.get("name") or f"Rule {index}")
        start_above = float(raw_rule["start_above"])
        stop_below = float(raw_rule["stop_below"])
        if stop_below >= start_above:
            raise ValueError(f"Rule '{name}' must have stop_below < start_above")
        manual_run_minutes = _require_positive_number(
            raw_rule["manual_run_minutes"],
            f"rules[{index}].manual_run_minutes",
        )

        max_runs = raw_rule.get("max_runs_per_day")
        cooldown = raw_rule.get("cooldown_minutes")

        rules.append(
            TemperatureRule(
                name=name,
                device_id=str(raw_rule["device_id"]),
                station=int(raw_rule["station"]),
                start_above=start_above,
                stop_below=stop_below,
                manual_run_minutes=manual_run_minutes,
                enabled=bool(raw_rule.get("enabled", True)),
                max_runs_per_day=(
                    _require_positive_int(max_runs, f"rules[{index}].max_runs_per_day")
                    if max_runs is not None
                    else None
                ),
                cooldown_minutes=(
                    _require_positive_int(cooldown, f"rules[{index}].cooldown_minutes")
                    if cooldown is not None
                    else None
                ),
                allowed_hours_local=_parse_allowed_hours(
                    raw_rule.get("allowed_hours_local")
                ),
            )
        )

    return AppConfig(
        path=config_path,
        bhyve=bhyve,
        weather=weather,
        controller=controller,
        rules=rules,
    )


def load_app_config(config_path: Path) -> AppConfig:
    resolved_path = config_path.expanduser().resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")
    data = load_raw_config(resolved_path)
    return parse_app_config(data, resolved_path)
