from __future__ import annotations

import asyncio
import json
import logging
import re
import socket
import threading
import webbrowser
from contextlib import suppress
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
from .controller import BhyveTemperatureService, current_station, parse_orbit_timestamp
from .weather import OpenMeteoClient

LOGGER = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "web"

SENSOR_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _default_automation_status() -> dict[str, Any]:
    return {
        "running": False,
        "paused": False,
        "paused_at": None,
        "last_cycle_started_at": None,
        "last_cycle_completed_at": None,
        "last_cycle_error": None,
        "last_cycle_actions_applied": 0,
        "poll_interval_seconds": None,
    }


def _capture_resume_candidates(latest_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not latest_payload:
        return []
    candidates: list[dict[str, Any]] = []
    for entry in latest_payload.get("active_watering", []):
        if entry.get("source") != "program":
            continue
        ends_at = parse_orbit_timestamp(entry.get("ends_at"))
        if ends_at is None:
            continue
        candidates.append(
            {
                "device_id": str(entry.get("device_id") or ""),
                "station": int(entry.get("station") or 0),
                "ends_at": ends_at.isoformat(),
            }
        )
    return [item for item in candidates if item["device_id"] and item["station"] > 0]


async def _automation_loop(app: web.Application) -> None:
    config_path: Path = app["config_path"]
    status: dict[str, Any] = app["automation_status"]

    while True:
        poll_interval_seconds = 30
        status["last_cycle_started_at"] = datetime.now().astimezone().isoformat()
        try:
            config = load_app_config(config_path)
            poll_interval_seconds = max(1, int(config.bhyve.poll_interval_seconds))
            status["poll_interval_seconds"] = poll_interval_seconds
            if app.get("automation_paused", False):
                status["last_cycle_actions_applied"] = 0
                status["last_cycle_error"] = None
            else:
                service = BhyveTemperatureService(config)
                report = await service.run_cycle(apply_changes=True)
                status["last_cycle_actions_applied"] = sum(1 for decision in report.decisions if decision.applied)
                status["last_cycle_error"] = None
                app["latest_status_payload"] = _json_safe(
                    {
                        "temperature": asdict(report.temperature),
                        "forecast": asdict(report.forecast),
                        "delay_status": asdict(report.delay_status),
                        "decisions": [asdict(decision) for decision in report.decisions],
                        "next_trigger": asdict(report.next_trigger),
                        "trigger_forecasts": [asdict(f) for f in report.trigger_forecasts],
                        "active_watering": [asdict(active) for active in report.active_watering],
                        "recent_history": service.get_recent_history(30),
                    }
                )
                LOGGER.debug(
                    "Web UI automation cycle completed. applied_actions=%s",
                    status["last_cycle_actions_applied"],
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            status["last_cycle_error"] = str(exc)
            LOGGER.exception("Web UI automation cycle failed")
        finally:
            status["last_cycle_completed_at"] = datetime.now().astimezone().isoformat()

        await asyncio.sleep(poll_interval_seconds)


async def _automation_context(app: web.Application):
    status: dict[str, Any] = app["automation_status"]
    status["running"] = True
    task = asyncio.create_task(_automation_loop(app), name="bhyve-web-automation")
    app["automation_task"] = task
    try:
        yield
    finally:
        status["running"] = False
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def _parse_sensor_message(message: str) -> dict[str, Any]:
    payload = json.loads(message)
    if not isinstance(payload, dict):
        raise ValueError("Sensor payload must be a JSON object")
    return payload


async def _ingest_sensor_payload(
    app: web.Application,
    payload: dict[str, Any],
    *,
    source_override: str | None = None,
) -> None:
    config_path: Path = app["config_path"]
    device_id = payload.get("device_id")
    station = payload.get("station")
    reading = {
        "temperature": _parse_sensor_number(payload.get("temperature")),
        "humidity": _parse_sensor_number(payload.get("humidity")),
        "humidity_percent": _parse_sensor_number(payload.get("humidity_percent")),
        "soil_moisture": _parse_sensor_number(payload.get("soil_moisture")),
        "soil_moisture_percent": _parse_sensor_number(payload.get("soil_moisture_percent")),
        "wind_speed": _parse_sensor_number(payload.get("wind_speed")),
        "wind_speed_mph": _parse_sensor_number(payload.get("wind_speed_mph")),
        "cloud_cover": _parse_sensor_number(payload.get("cloud_cover")),
        "cloud_cover_percent": _parse_sensor_number(payload.get("cloud_cover_percent")),
        "motion_detected": _parse_sensor_bool(
            payload.get("motion_detected") if "motion_detected" in payload else payload.get("motion")
        ),
        "observed_at": payload.get("observed_at") or datetime.now().astimezone().isoformat(),
        "source": source_override or str(payload.get("source") or "esp32"),
    }
    if device_id is not None:
        device_id = str(device_id).strip() or None
    if station in {None, ""}:
        station = None
    else:
        station = int(station)
    service = await _build_service(config_path)
    service.record_sensor_reading(device_id=device_id, station=station, reading=reading)


async def _serial_ingest_loop(app: web.Application) -> None:
    config = load_app_config(app["config_path"])
    serial_cfg = config.ingest.serial
    if not serial_cfg.enabled:
        return
    if not serial_cfg.port:
        LOGGER.warning("Serial ingest enabled but no port configured")
        return

    try:
        import serial  # type: ignore[import-not-found]
    except ImportError:
        LOGGER.warning("Serial ingest requested but pyserial is not installed")
        return

    while True:
        try:
            LOGGER.info("Starting serial sensor ingest on %s", serial_cfg.port)
            with serial.Serial(serial_cfg.port, serial_cfg.baudrate, timeout=serial_cfg.read_timeout_seconds) as client:
                while True:
                    raw = await asyncio.to_thread(client.readline)
                    if not raw:
                        continue
                    message = raw.decode("utf-8", errors="ignore").strip()
                    if not message:
                        continue
                    payload = _parse_sensor_message(message)
                    await _ingest_sensor_payload(app, payload, source_override="serial")
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Serial sensor ingest disconnected: %s", exc)
            await asyncio.sleep(serial_cfg.reconnect_seconds)


async def _bluetooth_ingest_loop(app: web.Application) -> None:
    config = load_app_config(app["config_path"])
    bluetooth_cfg = config.ingest.bluetooth
    if not bluetooth_cfg.enabled:
        return
    if not bluetooth_cfg.address or not bluetooth_cfg.characteristic_uuid:
        LOGGER.warning("Bluetooth ingest enabled but address/characteristic_uuid missing")
        return

    try:
        from bleak import BleakClient  # type: ignore[import-not-found]
    except ImportError:
        LOGGER.warning("Bluetooth ingest requested but bleak is not installed")
        return

    queue: asyncio.Queue[bytes] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _notification_handler(_sender: int, data: bytearray) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, bytes(data))

    while True:
        try:
            LOGGER.info("Starting Bluetooth sensor ingest from %s", bluetooth_cfg.address)
            async with BleakClient(bluetooth_cfg.address) as client:
                await client.start_notify(bluetooth_cfg.characteristic_uuid, _notification_handler)
                try:
                    while client.is_connected:
                        raw = await queue.get()
                        message = raw.decode("utf-8", errors="ignore").strip()
                        if not message:
                            continue
                        payload = _parse_sensor_message(message)
                        await _ingest_sensor_payload(app, payload, source_override="bluetooth")
                finally:
                    with suppress(Exception):
                        await client.stop_notify(bluetooth_cfg.characteristic_uuid)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Bluetooth sensor ingest disconnected: %s", exc)
            await asyncio.sleep(bluetooth_cfg.reconnect_seconds)


async def _sensor_ingest_context(app: web.Application):
    tasks = [
        asyncio.create_task(_serial_ingest_loop(app), name="bhyve-serial-ingest"),
        asyncio.create_task(_bluetooth_ingest_loop(app), name="bhyve-bluetooth-ingest"),
    ]
    app["sensor_ingest_tasks"] = tasks
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _parse_sensor_number(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        match = SENSOR_NUMBER_RE.search(value.replace(",", ""))
        if match is None:
            return None
        return float(match.group(0))
    return None


def _parse_sensor_bool(value: Any) -> bool | None:
    if value in {None, ""}:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, float):
        return value != 0.0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on", "detected", "motion", "active"}:
            return True
        if normalized in {"false", "0", "no", "off", "clear", "inactive", "none"}:
            return False
        if "motion" in normalized and "detect" in normalized:
            return True
    return None


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
    # Force next status call to rebuild from current config instead of returning stale cached cycle data.
    request.app["latest_status_payload"] = None
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
    automation_status: dict[str, Any] = request.app["automation_status"]

    latest_payload: dict[str, Any] | None = request.app.get("latest_status_payload")
    if latest_payload is not None:
        payload = dict(latest_payload)
        payload["automation_status"] = automation_status
        return web.json_response(payload)

    try:
        service = await _build_service(config_path)
        report = await service.run_cycle(apply_changes=False)
    except Exception as exc:  # noqa: BLE001
        cycle_error = automation_status.get("last_cycle_error")
        if cycle_error:
            raise web.HTTPServiceUnavailable(
                text=(
                    "Weather service is temporarily unavailable. "
                    "Please retry in a moment. "
                    f"Last automation error: {cycle_error}"
                )
            ) from exc
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response(
        _json_safe(
            {
                "temperature": asdict(report.temperature),
                "forecast": asdict(report.forecast),
                "delay_status": asdict(report.delay_status),
                "decisions": [asdict(decision) for decision in report.decisions],
                "next_trigger": asdict(report.next_trigger),
                "trigger_forecasts": [asdict(f) for f in report.trigger_forecasts],
                "active_watering": [asdict(status) for status in report.active_watering],
                "recent_history": service.get_recent_history(30),
                "automation_status": automation_status,
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
        await service.start_manual_ui_watering(device_id, station, minutes)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    # Invalidate the cached status so the next /api/status call fetches fresh device state.
    request.app["latest_status_payload"] = None
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

    request.app["latest_status_payload"] = None
    return web.json_response({"ok": True, "message": f"Requested stop for device {device_id}."})


async def _resume_captured_runs(app: web.Application) -> int:
    candidates: list[dict[str, Any]] = app.get("automation_resume_candidates", [])
    if not candidates:
        return 0

    service = await _build_service(app["config_path"])
    devices = await service.list_devices()
    devices_by_id = {str(device.get("id")): device for device in devices}
    now = datetime.now().astimezone()
    resumed = 0

    for candidate in candidates:
        device_id = str(candidate.get("device_id") or "").strip()
        station = int(candidate.get("station") or 0)
        ends_at = parse_orbit_timestamp(candidate.get("ends_at"))
        if not device_id or station <= 0 or ends_at is None or ends_at <= now:
            continue
        device = devices_by_id.get(device_id)
        if device is None:
            continue
        if current_station(device) is not None:
            continue

        remaining_minutes = max(0.1, (ends_at - now).total_seconds() / 60.0)
        await service.start_manual_watering(device_id, station, remaining_minutes)
        resumed += 1

    app["automation_resume_candidates"] = []
    return resumed


async def handle_automation_stop(request: web.Request) -> web.Response:
    automation_status: dict[str, Any] = request.app["automation_status"]
    if request.app.get("automation_paused", False):
        return web.json_response({"ok": True, "message": "Automation already stopped.", "resumable_runs": len(request.app.get("automation_resume_candidates", []))})

    request.app["automation_paused"] = True
    request.app["automation_resume_candidates"] = _capture_resume_candidates(request.app.get("latest_status_payload"))
    automation_status["paused"] = True
    automation_status["paused_at"] = datetime.now().astimezone().isoformat()
    return web.json_response(
        {
            "ok": True,
            "message": "Automation stopped. Existing watering continues unchanged.",
            "resumable_runs": len(request.app["automation_resume_candidates"]),
        }
    )


async def handle_automation_resume(request: web.Request) -> web.Response:
    automation_status: dict[str, Any] = request.app["automation_status"]
    if not request.app.get("automation_paused", False):
        return web.json_response({"ok": True, "message": "Automation is already running.", "resumed_runs": 0})

    request.app["automation_paused"] = False
    automation_status["paused"] = False
    automation_status["paused_at"] = None
    resumed_runs = await _resume_captured_runs(request.app)
    request.app["latest_status_payload"] = None
    return web.json_response(
        {
            "ok": True,
            "message": "Automation resumed.",
            "resumed_runs": resumed_runs,
        }
    )


async def handle_sensor_ingest(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
        await _ingest_sensor_payload(request.app, payload)
    except Exception as exc:  # noqa: BLE001
        raise web.HTTPBadRequest(text=str(exc)) from exc

    return web.json_response({"ok": True, "message": "Sensor reading stored."})


def create_web_app(config_path: Path) -> web.Application:
    app = web.Application()
    app["config_path"] = config_path.expanduser().resolve()
    app["automation_status"] = _default_automation_status()
    app["automation_paused"] = False
    app["automation_resume_candidates"] = []
    app["latest_status_payload"] = None
    app.cleanup_ctx.append(_automation_context)
    app.cleanup_ctx.append(_sensor_ingest_context)
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_post("/api/config", handle_save_config)
    app.router.add_get("/api/geocode", handle_geocode)
    app.router.add_get("/api/devices", handle_list_devices)
    app.router.add_get("/api/status", handle_preview)
    app.router.add_get("/api/preview", handle_preview)
    app.router.add_post("/api/manual-water", handle_manual_water)
    app.router.add_post("/api/stop-water", handle_stop_water)
    app.router.add_post("/api/sensors", handle_sensor_ingest)
    app.router.add_post("/api/automation/stop", handle_automation_stop)
    app.router.add_post("/api/automation/start", handle_automation_resume)
    app.router.add_post("/api/automation/resume", handle_automation_resume)
    app.router.add_static("/static/", STATIC_DIR)
    return app


def launch_web_ui(config_path: Path, host: str, port: int, open_browser: bool = False) -> None:
    app = create_web_app(config_path)
    browser_host = "127.0.0.1" if host == "0.0.0.0" else host
    browser_url = f"http://{browser_host}:{port}"
    LOGGER.info("Starting BHyve web UI at %s", browser_url)
    if host == "0.0.0.0":
        lan_host = "127.0.0.1"
        with suppress(Exception):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect(("8.8.8.8", 80))
                lan_host = probe.getsockname()[0]
        LOGGER.info("LAN access URL: http://%s:%s", lan_host, port)
    if open_browser:
        threading.Timer(0.75, lambda: webbrowser.open(browser_url)).start()
    web.run_app(app, host=host, port=port)
