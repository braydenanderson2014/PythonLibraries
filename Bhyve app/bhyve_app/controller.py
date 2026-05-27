from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from aiohttp import ClientSession

from .bhyve_client import BhyveClient
from .config import AppConfig, ControllerSettings, TemperatureRule
from .state_store import StateStore
from .weather import OpenMeteoClient, TemperatureReading, WeatherForecast

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Decision:
    rule_name: str
    device_id: str
    station: int
    action: str
    reason: str
    applied: bool = False


@dataclass(slots=True)
class TriggerForecast:
    at: datetime | None
    rule_name: str | None
    detail: str


@dataclass(slots=True)
class WeatherDelayStatus:
    active: bool
    manual_active: bool
    automatic_active: bool
    manual_until: datetime | None
    max_precipitation_probability: float
    probability_threshold: int
    lookahead_hours: int
    detail: str


@dataclass(slots=True)
class CycleReport:
    temperature: TemperatureReading
    forecast: WeatherForecast
    delay_status: WeatherDelayStatus
    decisions: list[Decision]
    next_trigger: TriggerForecast


def parse_orbit_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.year <= 1971:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def current_station(device: dict[str, Any]) -> str | None:
    watering_status = (device.get("status") or {}).get("watering_status") or {}
    station = watering_status.get("current_station")
    if station is None:
        return None
    return str(station)


def is_device_watering(device: dict[str, Any]) -> bool:
    return current_station(device) is not None


def zone_is_watering(device: dict[str, Any], station: int) -> bool:
    return current_station(device) == str(station)


def within_allowed_hours(rule: TemperatureRule, now: datetime) -> bool:
    if rule.allowed_hours_local is None:
        return True
    start_hour, end_hour = rule.allowed_hours_local
    current_hour = now.hour
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    return current_hour >= start_hour or current_hour < end_hour


def next_allowed_time(rule: TemperatureRule, candidate: datetime) -> datetime:
    if rule.allowed_hours_local is None:
        return candidate

    start_hour, end_hour = rule.allowed_hours_local
    start_today = candidate.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_today = candidate.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    if start_hour < end_hour:
        if candidate < start_today:
            return start_today
        if candidate < end_today:
            return candidate
        return start_today + timedelta(days=1)

    if candidate >= start_today or candidate < end_today:
        return candidate
    return start_today


def build_weather_delay_status(
    controller: ControllerSettings,
    forecast: WeatherForecast,
    now: datetime,
) -> WeatherDelayStatus:
    manual_until = controller.manual_weather_delay_until
    manual_active = bool(manual_until and manual_until > now)
    max_probability = float(forecast.max_precipitation_probability)
    automatic_active = (
        controller.automatic_weather_delay_enabled
        and max_probability >= controller.automatic_weather_delay_probability_threshold
    )

    detail_parts: list[str] = []
    if manual_active and manual_until is not None:
        detail_parts.append(
            f"Manual weather delay is active until {manual_until.astimezone().strftime('%b %d, %I:%M %p')}."
        )
    if automatic_active:
        detail_parts.append(
            f"Forecast rain chance reaches {max_probability:.0f}% within the next {controller.automatic_weather_delay_lookahead_hours} hours."
        )
    if not detail_parts:
        detail_parts.append("No weather delay is active.")

    return WeatherDelayStatus(
        active=manual_active or automatic_active,
        manual_active=manual_active,
        automatic_active=automatic_active,
        manual_until=manual_until,
        max_precipitation_probability=max_probability,
        probability_threshold=controller.automatic_weather_delay_probability_threshold,
        lookahead_hours=controller.automatic_weather_delay_lookahead_hours,
        detail=" ".join(detail_parts),
    )


def evaluate_weather_delay(
    rule: TemperatureRule,
    *,
    active_run: dict[str, Any] | None,
    delay_status: WeatherDelayStatus,
) -> Decision | None:
    if not delay_status.active:
        return None

    if delay_status.manual_active:
        reason = "manual_weather_delay_active"
    elif delay_status.automatic_active:
        reason = "automatic_weather_delay_active"
    else:
        return None

    return Decision(
        rule.name,
        rule.device_id,
        rule.station,
        "stop" if active_run else "noop",
        reason,
    )


def next_safe_forecast_time(
    forecast: WeatherForecast,
    *,
    threshold: int,
    now: datetime,
) -> datetime | None:
    for entry in forecast.entries:
        if entry.at < now:
            continue
        if entry.precipitation_probability < threshold:
            return entry.at
    return None


def describe_trigger_blocker(rule: TemperatureRule, decision: Decision) -> str | None:
    if decision.reason == "temperature_below_start_threshold":
        return (
            f"{rule.name} is inside its allowed hours and waits for temperature above "
            f"{rule.start_above:g}."
        )
    if decision.reason == "device_busy_with_existing_watering":
        return f"{rule.name} is waiting for the device to finish its current watering cycle."
    if decision.reason == "native_schedule_starts_soon":
        return f"{rule.name} is paused because a native BHyve schedule starts soon."
    if decision.reason == "service_run_active":
        return f"{rule.name} already has a service-owned run active."
    if decision.reason == "active_run_missing_on_device":
        return f"{rule.name} is waiting for controller state to resync with the device."
    if decision.reason == "device_not_found":
        return f"{rule.name} points to a device that is not currently available."
    if decision.reason == "rule_disabled":
        return f"{rule.name} is disabled."
    if decision.reason == "manual_weather_delay_active":
        return f"{rule.name} is paused by a manual weather delay."
    if decision.reason == "automatic_weather_delay_active":
        return f"{rule.name} is paused by the automatic weather delay forecast rules."
    return None


def forecast_rule_trigger(
    rule: TemperatureRule,
    decision: Decision,
    *,
    now: datetime,
    last_run_started_at: datetime | None,
    controller: ControllerSettings,
    delay_status: WeatherDelayStatus | None = None,
    forecast: WeatherForecast | None = None,
) -> TriggerForecast | None:
    if decision.action == "start":
        return TriggerForecast(
            at=now,
            rule_name=rule.name,
            detail=f"{rule.name} would start on this controller cycle.",
        )

    if decision.action == "stop":
        return TriggerForecast(
            at=now,
            rule_name=rule.name,
            detail=f"{rule.name} would stop on this controller cycle.",
        )

    if decision.reason == "outside_allowed_hours":
        return TriggerForecast(
            at=next_allowed_time(rule, now),
            rule_name=rule.name,
            detail=f"{rule.name} is outside its allowed hours and can trigger again when the window reopens.",
        )

    if decision.reason == "cooldown_active" and last_run_started_at is not None:
        cooldown_minutes = rule.cooldown_minutes or controller.default_cooldown_minutes
        return TriggerForecast(
            at=next_allowed_time(rule, last_run_started_at + timedelta(minutes=cooldown_minutes)),
            rule_name=rule.name,
            detail=f"{rule.name} is cooling down before it can trigger again.",
        )

    if decision.reason == "daily_run_limit_reached":
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return TriggerForecast(
            at=next_allowed_time(rule, next_day),
            rule_name=rule.name,
            detail=f"{rule.name} has reached its daily run limit and must wait for the next day.",
        )

    if decision.reason == "manual_weather_delay_active" and delay_status is not None and delay_status.manual_until is not None:
        return TriggerForecast(
            at=next_allowed_time(rule, delay_status.manual_until),
            rule_name=rule.name,
            detail=f"{rule.name} can trigger again after the manual weather delay ends.",
        )

    if decision.reason == "automatic_weather_delay_active" and delay_status is not None and forecast is not None:
        safe_time = next_safe_forecast_time(
            forecast,
            threshold=delay_status.probability_threshold,
            now=now,
        )
        if safe_time is None:
            return None
        return TriggerForecast(
            at=next_allowed_time(rule, safe_time),
            rule_name=rule.name,
            detail=f"{rule.name} can trigger again when the forecast rain chance drops below {delay_status.probability_threshold}%.",
        )

    return None


def select_next_trigger(
    forecasts: list[TriggerForecast],
    blocking_details: list[str],
) -> TriggerForecast:
    if forecasts:
        return min(forecasts, key=lambda forecast: forecast.at)

    if blocking_details:
        return TriggerForecast(at=None, rule_name=None, detail=blocking_details[0])

    return TriggerForecast(
        at=None,
        rule_name=None,
        detail="No enabled rules currently have a predictable next trigger.",
    )


def evaluate_rule(
    rule: TemperatureRule,
    device: dict[str, Any],
    *,
    temperature: float,
    now: datetime,
    active_run: dict[str, Any] | None,
    last_run_started_at: datetime | None,
    runs_today: int,
    controller: ControllerSettings,
) -> Decision:
    if not rule.enabled:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "rule_disabled")

    if active_run:
        if not zone_is_watering(device, rule.station):
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "noop",
                "active_run_missing_on_device",
            )
        if temperature <= rule.stop_below:
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "stop",
                "temperature_below_stop_threshold",
            )
        if not within_allowed_hours(rule, now):
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "stop",
                "outside_allowed_hours",
            )
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "service_run_active",
        )

    if is_device_watering(device):
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "device_busy_with_existing_watering",
        )

    if not within_allowed_hours(rule, now):
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "outside_allowed_hours",
        )

    next_start_time = parse_orbit_timestamp((device.get("status") or {}).get("next_start_time"))
    if next_start_time is not None:
        seconds_until_schedule = (next_start_time - now).total_seconds()
        if 0 <= seconds_until_schedule <= controller.schedule_guard_minutes * 60:
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "noop",
                "native_schedule_starts_soon",
            )

    if temperature < rule.start_above:
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "temperature_below_start_threshold",
        )

    cooldown_minutes = rule.cooldown_minutes or controller.default_cooldown_minutes
    if last_run_started_at is not None and now - last_run_started_at < timedelta(
        minutes=cooldown_minutes
    ):
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "cooldown_active",
        )

    max_runs = rule.max_runs_per_day or controller.default_max_runs_per_day
    if runs_today >= max_runs:
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "daily_run_limit_reached",
        )

    return Decision(
        rule.name,
        rule.device_id,
        rule.station,
        "start",
        "temperature_above_start_threshold",
    )


def format_device_summary(device: dict[str, Any]) -> str:
    lines = [
        (
            f"{device.get('name', 'Unnamed device')} | id={device.get('id')} "
            f"| type={device.get('type')} | connected={device.get('is_connected')}"
        )
    ]
    status = device.get("status") or {}
    next_start = status.get("next_start_time")
    watering_status = status.get("watering_status")
    lines.append(f"  next_start_time={next_start}")
    lines.append(f"  watering_status={watering_status}")
    for zone in device.get("zones", []):
        lines.append(
            f"  station={zone.get('station')} | zone={zone.get('name', 'Unnamed zone')}"
        )
    return "\n".join(lines)


class BhyveTemperatureService:
    _scheduled_stops: dict[str, asyncio.Task[None]] = {}

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._state = StateStore(config.controller.state_file)

    @staticmethod
    def _scheduled_stop_key(device_id: str) -> str:
        return str(device_id)

    @staticmethod
    def _planned_runtime(minutes: float) -> tuple[int, float | None]:
        requested_seconds = float(minutes) * 60.0
        orbit_minutes = max(1, math.ceil(minutes))
        orbit_seconds = orbit_minutes * 60.0
        if math.isclose(requested_seconds, orbit_seconds, rel_tol=0.0, abs_tol=1e-9):
            return orbit_minutes, None
        return orbit_minutes, requested_seconds

    @classmethod
    def _cancel_scheduled_stop(cls, device_id: str) -> None:
        task = cls._scheduled_stops.pop(cls._scheduled_stop_key(device_id), None)
        if task is not None:
            task.cancel()

    @classmethod
    def _track_scheduled_stop(cls, device_id: str, task: asyncio.Task[None]) -> None:
        key = cls._scheduled_stop_key(device_id)
        cls._scheduled_stops[key] = task

        def _cleanup(completed: asyncio.Task[None]) -> None:
            current = cls._scheduled_stops.get(key)
            if current is completed:
                cls._scheduled_stops.pop(key, None)
            try:
                completed.result()
            except asyncio.CancelledError:
                LOGGER.debug("Cancelled scheduled stop for %s", device_id)
            except Exception:  # noqa: BLE001
                LOGGER.exception("Scheduled stop failed for %s", device_id)

        task.add_done_callback(_cleanup)

    async def _build_clients(self) -> tuple[ClientSession, BhyveClient, OpenMeteoClient]:
        timeout = BhyveClient.build_timeout(self._config.bhyve.request_timeout_seconds)
        session = ClientSession(timeout=timeout)
        bhyve_client = BhyveClient(
            self._config.bhyve.email,
            self._config.bhyve.password,
            session,
            api_key=self._config.bhyve.api_key,
        )
        weather_client = OpenMeteoClient(session)
        return session, bhyve_client, weather_client

    async def list_devices(self) -> list[dict[str, Any]]:
        session, bhyve_client, _ = await self._build_clients()
        try:
            return await bhyve_client.get_devices()
        finally:
            await session.close()

    async def _send_start_manual_watering(
        self,
        device_id: str,
        station: int,
        minutes: int,
    ) -> None:
        session, bhyve_client, _ = await self._build_clients()
        try:
            await bhyve_client.start_manual_watering(device_id, station, minutes)
        finally:
            await session.close()

    async def _send_stop_manual_watering(self, device_id: str) -> None:
        session, bhyve_client, _ = await self._build_clients()
        try:
            await bhyve_client.stop_manual_watering(device_id)
        finally:
            await session.close()

    async def _stop_manual_watering_after_delay(self, device_id: str, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        await self._send_stop_manual_watering(device_id)

    async def start_manual_watering(
        self,
        device_id: str,
        station: int,
        minutes: float,
        *,
        wait_for_scheduled_stop: bool = False,
    ) -> None:
        orbit_minutes, delayed_stop_seconds = self._planned_runtime(minutes)
        self._cancel_scheduled_stop(device_id)
        await self._send_start_manual_watering(device_id, station, orbit_minutes)
        if delayed_stop_seconds is None:
            return

        if wait_for_scheduled_stop:
            await self._stop_manual_watering_after_delay(device_id, delayed_stop_seconds)
            return

        task = asyncio.create_task(
            self._stop_manual_watering_after_delay(device_id, delayed_stop_seconds)
        )
        self._track_scheduled_stop(device_id, task)

    async def stop_manual_watering(self, device_id: str) -> None:
        self._cancel_scheduled_stop(device_id)
        await self._send_stop_manual_watering(device_id)

    async def run_cycle(
        self,
        *,
        apply_changes: bool,
        wait_for_scheduled_stops: bool = False,
    ) -> CycleReport:
        session, bhyve_client, weather_client = await self._build_clients()
        try:
            weather_snapshot = await weather_client.get_weather_snapshot(
                self._config.weather.latitude,
                self._config.weather.longitude,
                self._config.weather.temperature_unit,
                lookahead_hours=self._config.controller.automatic_weather_delay_lookahead_hours,
            )
            devices = await bhyve_client.get_devices()
        finally:
            await session.close()

        temperature = weather_snapshot.temperature
        forecast = weather_snapshot.forecast
        devices_by_id = {str(device.get("id")): device for device in devices}
        decisions: list[Decision] = []
        trigger_forecasts: list[TriggerForecast] = []
        blocking_details: list[str] = []
        busy_devices = {device_id for device_id, device in devices_by_id.items() if is_device_watering(device)}
        state_changed = False
        now = datetime.now().astimezone()
        delay_status = build_weather_delay_status(self._config.controller, forecast, now)

        if not apply_changes:
            LOGGER.info("Running in dry-run mode")

        for rule in self._config.rules:
            device = devices_by_id.get(rule.device_id)
            if device is None:
                decisions.append(
                    Decision(
                        rule.name,
                        rule.device_id,
                        rule.station,
                        "noop",
                        "device_not_found",
                    )
                )
                continue

            active_run = self._state.get_active_run(rule.device_id, rule.station)
            if active_run and not zone_is_watering(device, rule.station):
                self._state.clear_active_run(rule.device_id, rule.station)
                active_run = None
                state_changed = True

            last_run_started_at = self._state.last_run_started_at(
                rule.device_id,
                rule.station,
            )
            runs_today = self._state.runs_today(rule.device_id, rule.station, now)

            delay_decision = evaluate_weather_delay(
                rule,
                active_run=active_run,
                delay_status=delay_status,
            )

            if delay_decision is not None:
                decision = delay_decision
            else:
                decision = evaluate_rule(
                    rule,
                    device,
                    temperature=temperature.value,
                    now=now,
                    active_run=active_run,
                    last_run_started_at=last_run_started_at,
                    runs_today=runs_today,
                    controller=self._config.controller,
                )

            if decision.action == "start" and rule.device_id in busy_devices:
                decision.action = "noop"
                decision.reason = "device_already_handled_this_cycle"

            trigger_forecast = forecast_rule_trigger(
                rule,
                decision,
                now=now,
                last_run_started_at=last_run_started_at,
                controller=self._config.controller,
                delay_status=delay_status,
                forecast=forecast,
            )
            if trigger_forecast is not None:
                trigger_forecasts.append(trigger_forecast)
            else:
                blocker = describe_trigger_blocker(rule, decision)
                if blocker:
                    blocking_details.append(blocker)

            if apply_changes and decision.action == "start":
                await self.start_manual_watering(
                    rule.device_id,
                    rule.station,
                    rule.manual_run_minutes,
                    wait_for_scheduled_stop=wait_for_scheduled_stops,
                )
                self._state.set_active_run(
                    rule.device_id,
                    rule.station,
                    rule_name=rule.name,
                    started_at=temperature.observed_at,
                    requested_minutes=rule.manual_run_minutes,
                    trigger_temperature=temperature.value,
                )
                self._state.record_run(
                    rule.device_id,
                    rule.station,
                    temperature.observed_at,
                )
                busy_devices.add(rule.device_id)
                decision.applied = True
                state_changed = True
                LOGGER.info(
                    "Started manual watering for %s station %s due to rule %s",
                    rule.device_id,
                    rule.station,
                    rule.name,
                )

            if apply_changes and decision.action == "stop":
                await self.stop_manual_watering(rule.device_id)
                self._state.clear_active_run(rule.device_id, rule.station)
                busy_devices.add(rule.device_id)
                decision.applied = True
                state_changed = True
                LOGGER.info(
                    "Stopped manual watering for %s due to rule %s",
                    rule.device_id,
                    rule.name,
                )

            decisions.append(decision)

        if state_changed:
            self._state.save()

        return CycleReport(
            temperature=temperature,
            forecast=forecast,
            delay_status=delay_status,
            decisions=decisions,
            next_trigger=select_next_trigger(trigger_forecasts, blocking_details),
        )
