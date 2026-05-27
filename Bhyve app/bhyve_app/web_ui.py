from __future__ import annotations

import logging
import threading
import webbrowser
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web

from .config import (
    default_config_template,
    load_app_config,
    looks_like_env_var_name,
    load_raw_config,
    parse_app_config,
    save_raw_config,
)
from .controller import BhyveTemperatureService
from .weather import OpenMeteoClient

LOGGER = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "web"


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validation_status(raw_config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    try:
        parsed = parse_app_config(raw_config, config_path)
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "error": str(exc), "rule_count": 0}

    return {"valid": True, "error": None, "rule_count": len(parsed.rules)}


def _bhyve_credential_mode(raw_bhyve: dict[str, Any]) -> str:
    api_key = str(raw_bhyve.get("api_key") or "").strip()
    api_key_env = str(raw_bhyve.get("api_key_env") or "").strip()
    password = str(raw_bhyve.get("password") or "").strip()
    password_env = str(raw_bhyve.get("password_env") or "").strip()
    if api_key:
        return "token"
    if api_key_env and looks_like_env_var_name(api_key_env):
        return "token"
    if api_key_env:
        return "token"
    if password:
        return "password"
    if password_env and looks_like_env_var_name(password_env):
        return "env"
    if password_env:
        return "password"
    return "env"


def sanitize_config_for_ui(raw_config: dict[str, Any]) -> dict[str, Any]:
    config = _deep_merge_dict(default_config_template(), raw_config)
    raw_bhyve = raw_config.get("bhyve") if isinstance(raw_config.get("bhyve"), dict) else {}
    bhyve = config.setdefault("bhyve", {})
    credential_mode = _bhyve_credential_mode(raw_bhyve)
    api_key = str(raw_bhyve.get("api_key") or "").strip()
    api_key_env = str(raw_bhyve.get("api_key_env") or "").strip()
    password_env = str(raw_bhyve.get("password_env") or "").strip()
    legacy_password_in_env = bool(password_env) and not looks_like_env_var_name(password_env)
    has_saved_password = bool(str(raw_bhyve.get("password") or "").strip()) or legacy_password_in_env
    has_saved_api_key = bool(api_key) or bool(api_key_env)
    bhyve["credential_mode"] = credential_mode
    bhyve["password_env"] = password_env if credential_mode == "env" else ""
    bhyve["password"] = ""
    bhyve["api_key"] = ""
    return {
        "config": config,
        "meta": {
            "has_saved_password": has_saved_password,
            "has_saved_api_key": has_saved_api_key,
            "credential_mode": credential_mode,
            "legacy_password_in_env": legacy_password_in_env,
        },
    }


def merge_ui_config(existing_config: dict[str, Any], incoming_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(incoming_config, dict):
        raise ValueError("Config payload must be a JSON object")

    merged = _deep_merge_dict(default_config_template(), incoming_config)
    existing_bhyve = existing_config.get("bhyve") if isinstance(existing_config.get("bhyve"), dict) else {}
    bhyve = merged.setdefault("bhyve", {})
    incoming_bhyve = incoming_config.get("bhyve") if isinstance(incoming_config.get("bhyve"), dict) else {}

    password = str(incoming_bhyve.get("password") or "").strip()
    password_env = str(incoming_bhyve.get("password_env") or "").strip()
    api_key = str(incoming_bhyve.get("api_key") or "").strip()
    clear_saved_password = bool(incoming_bhyve.get("clear_saved_password"))
    credential_mode = str(incoming_bhyve.get("credential_mode") or "env").strip().lower()

    existing_password = str(existing_bhyve.get("password") or "").strip()
    existing_password_env = str(existing_bhyve.get("password_env") or "").strip()
    existing_api_key = str(existing_bhyve.get("api_key") or "").strip()
    existing_api_key_env = str(existing_bhyve.get("api_key_env") or "").strip()
    existing_saved_password = existing_password
    if not existing_saved_password and existing_password_env and not looks_like_env_var_name(existing_password_env):
        existing_saved_password = existing_password_env

    existing_saved_api_key = existing_api_key
    if not existing_saved_api_key and existing_api_key_env and not looks_like_env_var_name(existing_api_key_env):
        existing_saved_api_key = existing_api_key_env

    bhyve.pop("password", None)
    bhyve.pop("password_env", None)
    bhyve.pop("api_key", None)
    bhyve.pop("api_key_env", None)
    bhyve.pop("credential_mode", None)

    if credential_mode == "token":
        if api_key:
            bhyve["api_key"] = api_key
        elif existing_saved_api_key:
            bhyve["api_key"] = existing_saved_api_key
        elif existing_api_key_env:
            bhyve["api_key_env"] = existing_api_key_env
        else:
            raise ValueError(
                "Paste an Orbit API token for Google-backed accounts or switch credential source"
            )
    elif credential_mode == "password":
        saved_password = password or ("" if clear_saved_password else existing_saved_password)
        if not saved_password:
            raise ValueError(
                "Enter a BHyve password or switch credential source to environment variable"
            )
        bhyve["password"] = saved_password
    else:
        env_name = password_env
        if not env_name and looks_like_env_var_name(existing_password_env):
            env_name = existing_password_env
        if not env_name:
            env_name = "BHYVE_PASSWORD"
        if not looks_like_env_var_name(env_name):
            raise ValueError(
                "Password env var must look like an environment variable name, such as BHYVE_PASSWORD"
            )
        bhyve["password_env"] = env_name

    if "clear_saved_password" in bhyve:
        bhyve.pop("clear_saved_password", None)

    return merged


def _load_config_payload(config_path: Path) -> dict[str, Any]:
    raw_config = load_raw_config(config_path)
    payload = sanitize_config_for_ui(raw_config)
    payload["meta"]["config_path"] = str(config_path.expanduser().resolve())
    payload["meta"]["is_default_template"] = not config_path.expanduser().resolve().exists()
    payload["validation"] = _validation_status(raw_config, config_path)
    return payload


def _serialize_device(device: dict[str, Any]) -> dict[str, Any]:
    status = device.get("status") or {}
    return {
        "id": str(device.get("id") or ""),
        "name": device.get("name") or "Unnamed device",
        "type": device.get("type") or "unknown",
        "is_connected": bool(device.get("is_connected")),
        "next_start_time": status.get("next_start_time"),
        "watering_status": status.get("watering_status"),
        "zones": [
            {
                "station": zone.get("station"),
                "name": zone.get("name") or f"Zone {zone.get('station')}",
                "smart_watering_enabled": zone.get("smart_watering_enabled"),
            }
            for zone in device.get("zones", [])
        ],
    }


async def _build_service(config_path: Path) -> BhyveTemperatureService:
    config = load_app_config(config_path)
    return BhyveTemperatureService(config)


async def handle_index(_request: web.Request) -> web.StreamResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def handle_get_config(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    return web.json_response(_load_config_payload(config_path))


async def handle_save_config(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=f"Invalid JSON payload: {exc}") from exc

    existing_config = load_raw_config(config_path) if config_path.expanduser().resolve().exists() else default_config_template()
    incoming_config = payload.get("config")
    try:
        merged_config = merge_ui_config(existing_config, incoming_config)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    save_raw_config(config_path, merged_config)
    return web.json_response(_load_config_payload(config_path))


async def handle_list_devices(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    try:
        service = await _build_service(config_path)
        devices = await service.list_devices()
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response({"devices": [_serialize_device(device) for device in devices]})


async def handle_preview(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    try:
        service = await _build_service(config_path)
        report = await service.run_cycle(apply_changes=False)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response(
        _json_safe(
            {
                "temperature": asdict(report.temperature),
                "forecast": asdict(report.forecast),
                "delay_status": asdict(report.delay_status),
                "decisions": [asdict(decision) for decision in report.decisions],
                "next_trigger": asdict(report.next_trigger),
            }
        )
    )


async def handle_geocode(request: web.Request) -> web.Response:
    query = str(request.query.get("query") or "").strip()
    if len(query) < 2:
        raise web.HTTPBadRequest(text="Enter at least two characters to search for a location")

    timeout = ClientTimeout(total=20)
    try:
        async with ClientSession(timeout=timeout) as session:
            weather_client = OpenMeteoClient(session)
            matches = await weather_client.search_locations(query)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response({"results": [asdict(match) for match in matches]})


async def handle_manual_water(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    try:
        payload = await request.json()
        device_id = str(payload["device_id"])
        station = int(payload["station"])
        minutes = float(payload["minutes"])
        service = await _build_service(config_path)
        await service.start_manual_watering(device_id, station, minutes)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response(
        {
            "ok": True,
            "message": f"Requested manual watering for device {device_id}, station {station} for {minutes} minutes.",
        }
    )


async def handle_stop_water(request: web.Request) -> web.Response:
    config_path: Path = request.app["config_path"]
    try:
        payload = await request.json()
        device_id = str(payload["device_id"])
        service = await _build_service(config_path)
        await service.stop_manual_watering(device_id)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response({"ok": True, "message": f"Requested stop for device {device_id}."})


def create_web_app(config_path: Path) -> web.Application:
    app = web.Application()
    app["config_path"] = config_path.expanduser().resolve()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_post("/api/config", handle_save_config)
    app.router.add_get("/api/geocode", handle_geocode)
    app.router.add_get("/api/devices", handle_list_devices)
    app.router.add_get("/api/status", handle_preview)
    app.router.add_get("/api/preview", handle_preview)
    app.router.add_post("/api/manual-water", handle_manual_water)
    app.router.add_post("/api/stop-water", handle_stop_water)
    app.router.add_static("/static/", STATIC_DIR)
    return app


def launch_web_ui(config_path: Path, host: str, port: int, open_browser: bool = False) -> None:
    app = create_web_app(config_path)
    url = f"http://{host}:{port}"
    LOGGER.info("Starting BHyve web UI at %s", url)
    if open_browser:
        threading.Timer(0.75, lambda: webbrowser.open(url)).start()
    web.run_app(app, host=host, port=port)
