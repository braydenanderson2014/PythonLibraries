from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from aiohttp import ClientSession

from .bhyve_client import BhyveClient
from .config import AppConfig, ControllerSettings, DevicePolicy, ScheduleRule, TemperatureRule
from .state_store import StateStore
from .weather import OpenMeteoClient, TemperatureReading, WeatherForecast

LOGGER = logging.getLogger(__name__)

WIND_SPEED_BLOCK_THRESHOLD_MPH = 15.0
SOIL_MOISTURE_TOO_WET_PERCENT = 35.0
CLOUD_COVER_CONSERVATIVE_THRESHOLD_PERCENT = 70.0
CLOUD_COVER_MAX_START_BONUS_F = 5.0
# How many minutes after a scheduled time the rule remains eligible to fire.
SCHEDULE_TRIGGER_WINDOW_MINUTES = 5


@dataclass(slots=True)
class Decision:
    rule_name: str
    device_id: str
    station: int
    action: str
    reason: str
    applied: bool = False
    cooldown_remaining_seconds: int | None = None
    pause_remaining_seconds: int | None = None


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
    trigger_forecasts: list[TriggerForecast]
    active_watering: list["ActiveWateringStatus"]


@dataclass(slots=True)
class ActiveWateringStatus:
    device_id: str
    device_name: str
    station: int
    source: str
    rule_name: str | None
    started_at: datetime | None
    ends_at: datetime | None


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


def effective_cooldown_minutes(
    rule: TemperatureRule,
    controller: ControllerSettings,
    temperature: float | None,
) -> int:
    if rule.cooldown_minutes_range is None:
        return rule.cooldown_minutes or controller.default_cooldown_minutes

    min_minutes, max_minutes = rule.cooldown_minutes_range
    if temperature is None or rule.start_above <= rule.stop_below:
        return max_minutes

    if temperature <= rule.start_above:
        return max_minutes

    span = max(1.0, rule.start_above - rule.stop_below)
    if temperature >= rule.start_above + span:
        return min_minutes

    # Move from max -> min cooldown as temperature climbs above start threshold.
    normalized = (temperature - rule.start_above) / span
    computed = max_minutes - (max_minutes - min_minutes) * normalized
    return int(round(computed))


def _sensor_number(sensor_reading: dict[str, Any] | None, *keys: str) -> float | None:
    if not sensor_reading:
        return None
    for key in keys:
        value = sensor_reading.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _effective_temperature_for_rule(temperature: float, sensor_reading: dict[str, Any] | None) -> float:
    sensor_temperature = _sensor_number(sensor_reading, "temperature", "temp")
    return sensor_temperature if sensor_temperature is not None else temperature


def _cloud_adjusted_start_threshold(rule: TemperatureRule, sensor_reading: dict[str, Any] | None) -> float:
    cloud_cover = _sensor_number(sensor_reading, "cloud_cover_percent", "cloud_cover")
    if cloud_cover is None:
        return rule.start_above
    cloud_cover = max(0.0, min(100.0, cloud_cover))
    if cloud_cover < CLOUD_COVER_CONSERVATIVE_THRESHOLD_PERCENT:
        return rule.start_above
    cloud_bonus = (cloud_cover / 100.0) * CLOUD_COVER_MAX_START_BONUS_F
    return rule.start_above + cloud_bonus


def _sensor_bool(sensor_reading: dict[str, Any] | None, *keys: str) -> bool:
    if not sensor_reading:
        return False
    for key in keys:
        value = sensor_reading.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on", "detected", "motion", "active"}:
                return True
            if normalized in {"false", "0", "no", "off", "clear", "inactive", "none"}:
                return False
    return False


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
    rule: TemperatureRule | ScheduleRule,
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


def describe_trigger_blocker(rule: TemperatureRule | ScheduleRule, decision: Decision) -> str | None:
    if decision.reason == "temperature_below_start_threshold":
        assert isinstance(rule, TemperatureRule)
        return (
            f"{rule.name} is inside its allowed hours and waits for temperature above "
            f"{rule.start_above:g}."
        )
    if decision.reason == "device_busy_with_existing_watering":
        return f"{rule.name} is waiting for the device to finish its current watering cycle."
    if decision.reason == "motion_pause_active":
        return f"{rule.name} is paused because motion was detected nearby."
    if decision.reason == "windy_conditions_active":
        return f"{rule.name} is paused because wind is too strong for effective watering."
    if decision.reason == "soil_moisture_sufficient":
        return f"{rule.name} is paused because the soil is already moist enough."
    if decision.reason == "cloudy_conditions_active":
        return f"{rule.name} is paused because cloudy conditions make watering less effective right now."
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
    if decision.reason == "outside_schedule_window":
        return f"{rule.name} is waiting for its next scheduled run time."
    if decision.reason == "not_a_scheduled_day":
        return f"{rule.name} is waiting for the next scheduled day."
    if decision.reason == "temperature_below_minimum":
        return f"{rule.name} is paused because the temperature is below the minimum threshold."
    return None


def forecast_rule_trigger(
    rule: TemperatureRule | ScheduleRule,
    decision: Decision,
    *,
    now: datetime,
    temperature: float | None,
    last_run_started_at: datetime | None,
    controller: ControllerSettings,
    delay_status: WeatherDelayStatus | None = None,
    forecast: WeatherForecast | None = None,
    sensor_reading: dict[str, Any] | None = None,
    motion_pause_until: datetime | None = None,
) -> TriggerForecast | None:
    if decision.action == "start":
        detail = (
            f"{rule.name}: scheduled time triggered — watering will start shortly."
            if isinstance(rule, ScheduleRule)
            else f"{rule.name}: temperature threshold met — watering will start shortly."
        )
        return TriggerForecast(at=now, rule_name=rule.name, detail=detail)

    if decision.action == "stop":
        return TriggerForecast(
            at=now,
            rule_name=rule.name,
            detail=f"{rule.name}: temperature has dropped — watering will stop shortly.",
        )

    # Schedule-rule-specific forecasts.
    if isinstance(rule, ScheduleRule):
        if decision.reason in ("outside_schedule_window", "not_a_scheduled_day", "temperature_below_minimum"):
            next_trigger = next_schedule_trigger(rule, now)
            if next_trigger is None:
                return None
            return TriggerForecast(
                at=next_trigger,
                rule_name=rule.name,
                detail=f"{rule.name} will next run at {next_trigger.astimezone().strftime('%a %b %d, %I:%M %p')}.",
            )

        if decision.reason == "cooldown_active" and last_run_started_at is not None:
            cooldown_minutes = rule.cooldown_minutes or controller.default_cooldown_minutes
            expires_at = last_run_started_at + timedelta(minutes=cooldown_minutes)
            next_trigger = next_schedule_trigger(rule, expires_at)
            if next_trigger is None:
                return None
            return TriggerForecast(
                at=next_trigger,
                rule_name=rule.name,
                detail=f"{rule.name} is cooling down before it can trigger again.",
            )

        if decision.reason == "daily_run_limit_reached":
            next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_trigger = next_schedule_trigger(rule, next_day)
            if next_trigger is None:
                return None
            return TriggerForecast(
                at=next_trigger,
                rule_name=rule.name,
                detail=f"{rule.name} has reached its daily run limit and will run again tomorrow.",
            )

        if decision.reason == "manual_weather_delay_active" and delay_status is not None and delay_status.manual_until is not None:
            next_trigger = next_schedule_trigger(rule, delay_status.manual_until)
            if next_trigger is None:
                return None
            return TriggerForecast(
                at=next_trigger,
                rule_name=rule.name,
                detail=f"{rule.name} can trigger again after the manual weather delay ends.",
            )

        if decision.reason == "automatic_weather_delay_active" and delay_status is not None and forecast is not None:
            safe_time = next_safe_forecast_time(forecast, threshold=delay_status.probability_threshold, now=now)
            if safe_time is None:
                return None
            next_trigger = next_schedule_trigger(rule, safe_time)
            if next_trigger is None:
                return None
            return TriggerForecast(
                at=next_trigger,
                rule_name=rule.name,
                detail=f"{rule.name} can trigger again when the forecast rain chance drops below {delay_status.probability_threshold}%.",
            )

        return None

    # Temperature-rule forecasts.
    if decision.reason == "outside_allowed_hours":
        return TriggerForecast(
            at=next_allowed_time(rule, now),
            rule_name=rule.name,
            detail=f"{rule.name} is outside its allowed hours and can trigger again when the window reopens.",
        )

    if decision.reason == "temperature_below_start_threshold":
        assert isinstance(rule, TemperatureRule)
        # Temp not reached yet — schedule a re-check after one cooldown period so
        # the rule stays visible in the Upcoming Programs list with a real time.
        cooldown_minutes = effective_cooldown_minutes(rule, controller, temperature)
        at = next_allowed_time(rule, now + timedelta(minutes=cooldown_minutes))
        return TriggerForecast(
            at=at,
            rule_name=rule.name,
            detail=f"{rule.name} will re-check in {cooldown_minutes} min — waiting for temperature to reach {rule.start_above:g}°.",
        )

    if decision.reason == "cooldown_active" and last_run_started_at is not None:
        cooldown_minutes = effective_cooldown_minutes(rule, controller, temperature)
        return TriggerForecast(
            at=next_allowed_time(rule, last_run_started_at + timedelta(minutes=cooldown_minutes)),
            rule_name=rule.name,
            detail=f"{rule.name} is cooling down — will check conditions again after the cooldown ends.",
        )

    if decision.reason == "motion_pause_active" and motion_pause_until is not None:
        return TriggerForecast(
            at=next_allowed_time(rule, motion_pause_until),
            rule_name=rule.name,
            detail=f"{rule.name} is paused by motion detection until the pause ends.",
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
    timed = [f for f in forecasts if f.at is not None]
    if timed:
        return min(timed, key=lambda forecast: forecast.at)  # type: ignore[arg-type]

    if blocking_details:
        return TriggerForecast(at=None, rule_name=None, detail=blocking_details[0])

    return TriggerForecast(
        at=None,
        rule_name=None,
        detail="No enabled rules currently have a predictable next trigger.",
    )


def next_schedule_trigger(rule: ScheduleRule, now: datetime) -> datetime | None:
    """Return the next wall-clock moment this schedule rule will enter a trigger window."""
    if not rule.schedule_times:
        return None
    sorted_times = sorted(rule.schedule_times)
    for day_offset in range(8):  # look up to 7 days ahead
        candidate_day = now + timedelta(days=day_offset)
        weekday = candidate_day.weekday()
        if rule.schedule_days and weekday not in rule.schedule_days:
            continue
        for hour, minute in sorted_times:
            candidate = candidate_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate > now:
                return candidate
    return None


def evaluate_schedule_rule(
    rule: ScheduleRule,
    device: dict[str, Any],
    *,
    temperature: float,
    now: datetime,
    active_run: dict[str, Any] | None,
    last_run_started_at: datetime | None,
    runs_today: int,
    controller: ControllerSettings,
    sensor_reading: dict[str, Any] | None = None,
) -> Decision:
    if not rule.enabled:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "rule_disabled")

    if active_run:
        if not zone_is_watering(device, rule.station):
            return Decision(rule.name, rule.device_id, rule.station, "noop", "active_run_missing_on_device")
        return Decision(rule.name, rule.device_id, rule.station, "noop", "service_run_active")

    if is_device_watering(device):
        return Decision(rule.name, rule.device_id, rule.station, "noop", "device_busy_with_existing_watering")

    # Day-of-week guard.
    if rule.schedule_days and now.weekday() not in rule.schedule_days:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "not_a_scheduled_day")

    # Trigger-window guard: are we within SCHEDULE_TRIGGER_WINDOW_MINUTES of a scheduled time?
    in_window = False
    for hour, minute in rule.schedule_times:
        window_start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=SCHEDULE_TRIGGER_WINDOW_MINUTES)
        if window_start <= now < window_end:
            in_window = True
            break
    if not in_window:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "outside_schedule_window")

    # Minimum temperature guard (e.g., freeze protection).
    effective_temperature = _effective_temperature_for_rule(temperature, sensor_reading)
    if rule.min_temperature is not None and effective_temperature < rule.min_temperature:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "temperature_below_minimum")

    # Cooldown guard.
    cooldown_minutes = rule.cooldown_minutes or controller.default_cooldown_minutes
    if last_run_started_at is not None and now - last_run_started_at < timedelta(minutes=cooldown_minutes):
        cooldown_remaining = timedelta(minutes=cooldown_minutes) - (now - last_run_started_at)
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "cooldown_active",
            cooldown_remaining_seconds=max(1, int(math.ceil(cooldown_remaining.total_seconds()))),
        )

    # Daily limit guard.
    max_runs = rule.max_runs_per_day or controller.default_max_runs_per_day
    if runs_today >= max_runs:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "daily_run_limit_reached")

    return Decision(rule.name, rule.device_id, rule.station, "start", "scheduled_time_triggered")


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
    sensor_reading: dict[str, Any] | None = None,
) -> Decision:
    if not rule.enabled:
        return Decision(rule.name, rule.device_id, rule.station, "noop", "rule_disabled")

    if active_run:
        effective_temperature = _effective_temperature_for_rule(temperature, sensor_reading)
        if not zone_is_watering(device, rule.station):
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "noop",
                "active_run_missing_on_device",
            )
        if effective_temperature <= rule.stop_below:
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

    effective_temperature = _effective_temperature_for_rule(temperature, sensor_reading)
    wind_speed = _sensor_number(sensor_reading, "wind_speed_mph", "wind_speed")
    soil_moisture = _sensor_number(sensor_reading, "soil_moisture_percent", "soil_moisture")
    if wind_speed is not None and wind_speed >= WIND_SPEED_BLOCK_THRESHOLD_MPH:
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "windy_conditions_active",
        )
    if soil_moisture is not None and soil_moisture >= SOIL_MOISTURE_TOO_WET_PERCENT:
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "soil_moisture_sufficient",
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

    adjusted_start_threshold = _cloud_adjusted_start_threshold(rule, sensor_reading)
    cloud_cover = _sensor_number(sensor_reading, "cloud_cover_percent", "cloud_cover")
    if effective_temperature < adjusted_start_threshold:
        if cloud_cover is not None and cloud_cover >= CLOUD_COVER_CONSERVATIVE_THRESHOLD_PERCENT:
            return Decision(
                rule.name,
                rule.device_id,
                rule.station,
                "noop",
                "cloudy_conditions_active",
            )
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "temperature_below_start_threshold",
        )

    cooldown_minutes = effective_cooldown_minutes(rule, controller, effective_temperature)
    if last_run_started_at is not None and now - last_run_started_at < timedelta(
        minutes=cooldown_minutes
    ):
        cooldown_remaining = timedelta(minutes=cooldown_minutes) - (now - last_run_started_at)
        return Decision(
            rule.name,
            rule.device_id,
            rule.station,
            "noop",
            "cooldown_active",
            cooldown_remaining_seconds=max(1, int(math.ceil(cooldown_remaining.total_seconds()))),
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
    def _planned_runtime(minutes: float) -> tuple[int, float]:
        """Return (orbit_minutes_to_send, stop_after_seconds).

        orbit_minutes is the integer value sent to BHyve (minimum 1).
        stop_after_seconds is when to send an explicit stop:
          - Fractional minutes: stop early at the exact requested duration.
          - Integer minutes: stop at the full orbit duration as a safety net
            because BHyve does not always auto-stop reliably.
        """
        requested_seconds = float(minutes) * 60.0
        orbit_minutes = max(1, math.ceil(minutes))
        orbit_seconds = float(orbit_minutes * 60)
        if math.isclose(requested_seconds, orbit_seconds, rel_tol=0.0, abs_tol=1e-9):
            return orbit_minutes, orbit_seconds
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
        if wait_for_scheduled_stop:
            await self._stop_manual_watering_after_delay(device_id, delayed_stop_seconds)
            return

        task = asyncio.create_task(
            self._stop_manual_watering_after_delay(device_id, delayed_stop_seconds)
        )
        self._track_scheduled_stop(device_id, task)

    async def start_manual_ui_watering(
        self,
        device_id: str,
        station: int,
        minutes: float,
    ) -> None:
        """Start a station from the web UI and mark it so the automation loop won't stop it."""
        now = datetime.now().astimezone()
        await self.start_manual_watering(device_id, station, minutes)
        self._state.set_active_external_watering(device_id, station, now, source="manual_ui")
        self._state.save()

    async def stop_manual_watering(self, device_id: str) -> None:
        self._cancel_scheduled_stop(device_id)
        await self._send_stop_manual_watering(device_id)

    def record_sensor_reading(
        self,
        *,
        device_id: str | None,
        station: int | None,
        reading: dict[str, Any],
    ) -> None:
        self._state.set_sensor_reading(device_id=device_id, station=station, reading=reading)
        self._state.save()

    def get_recent_history(self, limit: int = 30) -> list[dict[str, Any]]:
        return self._state.get_recent_history(limit)

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

        stop_external_devices = {
            rule.device_id for rule in self._config.rules if rule.stop_external_watering
        }
        # Devices that only allow stations explicitly covered by a rule.
        block_unlisted_devices = {
            dp.device_id for dp in self._config.device_policies if dp.block_unlisted_stations
        }
        force_stopped_devices: set[str] = set()

        # Detect external (non-program) watering sessions and record them in history.
        if apply_changes:
            for device_id, device in devices_by_id.items():
                station_str = current_station(device)
                existing_external = self._state.get_active_external_watering(device_id)
                if station_str is not None:
                    station_num = int(station_str)
                    program_run = self._state.get_active_run(device_id, station_num)
                    if program_run is None and existing_external is None:
                        self._state.set_active_external_watering(device_id, station_num, now)
                        self._state.record_run(
                            device_id,
                            station_num,
                            now,
                            source="timer",
                        )
                        state_changed = True
                        LOGGER.info(
                            "Detected external watering on device %s station %s",
                            device_id,
                            station_num,
                        )
                else:
                    if existing_external is not None:
                        self._state.clear_active_external_watering(device_id)
                        state_changed = True

        # Enforce block_unlisted_stations: stop any station running on a restricted device
        # that is not covered by any rule, and which is not a controller-owned run.
        if apply_changes:
            for device_id, device in devices_by_id.items():
                if device_id not in block_unlisted_devices:
                    continue
                if device_id in force_stopped_devices:
                    continue
                station_str = current_station(device)
                if station_str is None:
                    continue
                station_num = int(station_str)
                # Only stop if this is NOT a controller-owned run or a UI-initiated run.
                if self._state.get_active_run(device_id, station_num) is not None:
                    continue
                _ext = self._state.get_active_external_watering(device_id)
                if _ext and _ext.get("source") == "manual_ui":
                    continue
                LOGGER.warning(
                    "Device %s station %s is running but has no rule and block_unlisted_stations is on — stopping",
                    device_id,
                    station_num,
                )
                await self.stop_manual_watering(device_id)
                self._state.clear_active_external_watering(device_id)
                device.setdefault("status", {})["watering_status"] = None
                force_stopped_devices.add(device_id)
                busy_devices.add(device_id)
                decisions.append(
                    Decision(
                        f"device:{device_id}",
                        device_id,
                        station_num,
                        "stop",
                        "unlisted_station_blocked",
                        applied=True,
                    )
                )
                state_changed = True

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
            if active_run:
                _ar_started = parse_orbit_timestamp(active_run.get("started_at"))
                _ar_minutes = active_run.get("requested_minutes")
                _run_overdue = (
                    _ar_started is not None
                    and isinstance(_ar_minutes, (int, float))
                    and now >= _ar_started + timedelta(minutes=float(_ar_minutes) + 2)
                )
                if not zone_is_watering(device, rule.station) or _run_overdue:
                    if _run_overdue:
                        LOGGER.warning(
                            "Clearing overdue active_run for device %s station %s "
                            "(started %s, requested %.1f min) — treating as stale so "
                            "timer-initiated watering can be detected",
                            rule.device_id,
                            rule.station,
                            _ar_started,
                            _ar_minutes,
                        )
                    self._state.clear_active_run(rule.device_id, rule.station)
                    active_run = None
                    state_changed = True

            last_run_started_at = self._state.last_run_started_at(
                rule.device_id,
                rule.station,
            )
            runs_today = self._state.runs_today(rule.device_id, rule.station, now)
            sensor_reading = self._state.get_sensor_reading(rule.device_id, rule.station)
            motion_detected = _sensor_bool(sensor_reading, "motion_detected", "motion", "motion_state")
            motion_pause = self._state.get_motion_pause(rule.device_id, rule.station, now)
            motion_pause_until = parse_orbit_timestamp(motion_pause.get("expires_at")) if motion_pause else None

            if rule.pause_on_motion and motion_detected:
                pause_minutes = rule.motion_pause_minutes or 15
                motion_pause_until = now + timedelta(minutes=pause_minutes)
                self._state.set_motion_pause(
                    rule.device_id,
                    rule.station,
                    paused_at=now,
                    expires_at=motion_pause_until,
                    reason="motion_detected",
                )
                state_changed = True

            if motion_pause_until is not None and (motion_detected or motion_pause is not None):
                watering_active = is_device_watering(device)
                if apply_changes and watering_active:
                    await self.stop_manual_watering(rule.device_id)
                    if active_run is not None:
                        self._state.clear_active_run(rule.device_id, rule.station)
                        active_run = None
                    self._state.clear_active_external_watering(rule.device_id)
                    device.setdefault("status", {})["watering_status"] = None
                    state_changed = True
                decision = Decision(
                    rule.name,
                    rule.device_id,
                    rule.station,
                    "stop" if watering_active else "noop",
                    "motion_pause_active",
                    applied=apply_changes and watering_active,
                    pause_remaining_seconds=max(1, int((motion_pause_until - now).total_seconds())),
                )
                trigger_forecast = forecast_rule_trigger(
                    rule,
                    decision,
                    now=now,
                    temperature=temperature.value,
                    sensor_reading=sensor_reading,
                    last_run_started_at=last_run_started_at,
                    controller=self._config.controller,
                    delay_status=delay_status,
                    forecast=forecast,
                    motion_pause_until=motion_pause_until,
                )
                if trigger_forecast is not None:
                    trigger_forecasts.append(trigger_forecast)
                else:
                    blocker = describe_trigger_blocker(rule, decision)
                    if blocker:
                        blocking_details.append(blocker)
                        trigger_forecasts.append(TriggerForecast(at=None, rule_name=rule.name, detail=blocker))
                if decision.action == "start" and rule.device_id in busy_devices:
                    decision.action = "noop"
                    decision.reason = "device_already_handled_this_cycle"
                decisions.append(decision)
                busy_devices.add(rule.device_id)
                continue

            if (
                apply_changes
                and rule.device_id in stop_external_devices
                and rule.device_id not in force_stopped_devices
            ):
                current_station_text = current_station(device)
                if current_station_text is not None:
                    current_station_value = int(current_station_text)
                    if self._state.get_active_run(rule.device_id, current_station_value) is None:
                        _ext = self._state.get_active_external_watering(rule.device_id)
                        if not (_ext and _ext.get("source") == "manual_ui"):
                            await self.stop_manual_watering(rule.device_id)
                            self._state.clear_active_external_watering(rule.device_id)
                            device.setdefault("status", {})["watering_status"] = None
                            force_stopped_devices.add(rule.device_id)
                            busy_devices.add(rule.device_id)
                            decisions.append(
                                Decision(
                                    rule.name,
                                    rule.device_id,
                                    rule.station,
                                    "stop",
                                    "external_watering_auto_stopped",
                                    applied=True,
                                )
                            )
                            state_changed = True
                            LOGGER.info(
                                "Stopped non-program watering on %s because rule %s is configured to enforce controller-owned runs only",
                                rule.device_id,
                                rule.name,
                            )
                            continue

            delay_decision = evaluate_weather_delay(
                rule,
                active_run=active_run,
                delay_status=delay_status,
            )

            if delay_decision is not None:
                decision = delay_decision
            elif isinstance(rule, ScheduleRule):
                decision = evaluate_schedule_rule(
                    rule,
                    device,
                    temperature=temperature.value,
                    sensor_reading=sensor_reading,
                    now=now,
                    active_run=active_run,
                    last_run_started_at=last_run_started_at,
                    runs_today=runs_today,
                    controller=self._config.controller,
                )
            else:
                decision = evaluate_rule(
                    rule,
                    device,
                    temperature=temperature.value,
                    sensor_reading=sensor_reading,
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
                temperature=temperature.value,
                sensor_reading=sensor_reading,
                last_run_started_at=last_run_started_at,
                controller=self._config.controller,
                delay_status=delay_status,
                forecast=forecast,
                motion_pause_until=motion_pause_until,
            )
            if trigger_forecast is not None:
                trigger_forecasts.append(trigger_forecast)
            else:
                blocker = describe_trigger_blocker(rule, decision)
                if blocker:
                    blocking_details.append(blocker)
                    trigger_forecasts.append(TriggerForecast(at=None, rule_name=rule.name, detail=blocker))

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
                    source="program",
                    rule_name=rule.name,
                )
                device_status = device.setdefault("status", {})
                device_status["watering_status"] = {
                    "current_station": str(rule.station),
                    "source": "program",
                }
                busy_devices.add(rule.device_id)
                decision.applied = True
                state_changed = True
                LOGGER.info(
                    "Started manual watering for %s station %s due to rule %s",
                    rule.device_id,
                    rule.station,
                    rule.name,
                )

            if apply_changes and decision.action == "stop" and decision.reason != "motion_pause_active":
                await self.stop_manual_watering(rule.device_id)
                self._state.clear_active_run(rule.device_id, rule.station)
                device_status = device.setdefault("status", {})
                device_status["watering_status"] = None
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

        active_watering = self._collect_active_watering(devices_by_id, now)

        sorted_forecasts = sorted(
            (f for f in trigger_forecasts if f.at is not None),
            key=lambda f: f.at,  # type: ignore[arg-type]
        )
        waiting_forecasts = [f for f in trigger_forecasts if f.at is None and f.rule_name is not None]

        return CycleReport(
            temperature=temperature,
            forecast=forecast,
            delay_status=delay_status,
            decisions=decisions,
            next_trigger=select_next_trigger(trigger_forecasts, blocking_details),
            trigger_forecasts=sorted_forecasts + waiting_forecasts,
            active_watering=active_watering,
        )

    def _collect_active_watering(
        self,
        devices_by_id: dict[str, dict[str, Any]],
        now: datetime,
    ) -> list[ActiveWateringStatus]:
        statuses: list[ActiveWateringStatus] = []
        for device_id, device in devices_by_id.items():
            station_text = current_station(device)
            if station_text is None:
                continue

            try:
                station = int(station_text)
            except (TypeError, ValueError):
                continue

            source = "timer"
            rule_name: str | None = None
            started_at: datetime | None = None
            ends_at: datetime | None = None

            active_run = self._state.get_active_run(device_id, station)
            if active_run is not None:
                source = "program"
                rule_name = active_run.get("rule_name")
                started_at = parse_orbit_timestamp(active_run.get("started_at"))
                requested_minutes = active_run.get("requested_minutes")
                if started_at is not None and isinstance(requested_minutes, (int, float)):
                    ends_at = started_at + timedelta(minutes=float(requested_minutes))

            statuses.append(
                ActiveWateringStatus(
                    device_id=device_id,
                    device_name=str(device.get("name") or "Unnamed device"),
                    station=station,
                    source=source,
                    rule_name=rule_name,
                    started_at=started_at,
                    ends_at=ends_at,
                )
            )

        return statuses
