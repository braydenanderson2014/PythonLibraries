from __future__ import annotations

from unittest.mock import AsyncMock, Mock
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bhyve_app.config import AppConfig, BhyveSettings, ControllerSettings, TemperatureRule, WeatherSettings
from bhyve_app.controller import (
    BhyveTemperatureService,
    build_weather_delay_status,
    evaluate_weather_delay,
    evaluate_rule,
    forecast_rule_trigger,
)
from bhyve_app.weather import ForecastEntry, WeatherForecast


def build_device(*, watering_status=None, next_start_time=None):
    return {
        "id": "device-1",
        "status": {
            "watering_status": watering_status,
            "next_start_time": next_start_time,
        },
    }


def build_forecast(base_time: datetime, probabilities: list[float]) -> WeatherForecast:
    entries = [
        ForecastEntry(
            at=base_time + timedelta(hours=index),
            temperature=80.0 - index,
            precipitation_probability=probability,
            precipitation=0.1 if probability > 0 else 0.0,
        )
        for index, probability in enumerate(probabilities)
    ]
    return WeatherForecast(
        entries=entries,
        max_precipitation_probability=max(probabilities, default=0.0),
        total_precipitation=sum(entry.precipitation for entry in entries),
        lookahead_hours=len(probabilities),
    )


class EvaluateRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rule = TemperatureRule(
            name="Heat boost",
            device_id="device-1",
            station=1,
            start_above=88,
            stop_below=78,
            manual_run_minutes=10,
            enabled=True,
            max_runs_per_day=2,
            cooldown_minutes=120,
            allowed_hours_local=(10, 19),
        )
        self.controller = ControllerSettings(
            schedule_guard_minutes=30,
            default_cooldown_minutes=120,
            default_max_runs_per_day=3,
            automatic_weather_delay_enabled=False,
            automatic_weather_delay_probability_threshold=60,
            automatic_weather_delay_lookahead_hours=12,
            manual_weather_delay_until=None,
            state_file=Path(".bhyve_state.json"),
        )
        self.now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)

    def test_starts_when_hot_and_idle(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "start")
        self.assertEqual(decision.reason, "temperature_above_start_threshold")

    def test_does_not_start_when_schedule_is_soon(self) -> None:
        next_start = (self.now + timedelta(minutes=15)).isoformat()
        decision = evaluate_rule(
            self.rule,
            build_device(next_start_time=next_start),
            temperature=92,
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "native_schedule_starts_soon")

    def test_stops_service_run_when_temperature_cools(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(watering_status={"current_station": 1}),
            temperature=75,
            now=self.now,
            active_run={"started_at": self.now.isoformat()},
            last_run_started_at=self.now - timedelta(hours=4),
            runs_today=1,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "stop")
        self.assertEqual(decision.reason, "temperature_below_stop_threshold")

    def test_respects_cooldown(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            now=self.now,
            active_run=None,
            last_run_started_at=self.now - timedelta(minutes=30),
            runs_today=1,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "cooldown_active")

    def test_forecast_next_trigger_uses_allowed_window_reopen_time(self) -> None:
        now = datetime(2026, 5, 26, 20, 30, tzinfo=timezone.utc)
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            now=now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )

        forecast = forecast_rule_trigger(
            self.rule,
            decision,
            now=now,
            last_run_started_at=None,
            controller=self.controller,
        )

        self.assertIsNotNone(forecast)
        self.assertEqual(forecast.at, datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc))

    def test_forecast_next_trigger_uses_cooldown_end(self) -> None:
        last_run_started_at = self.now - timedelta(minutes=30)
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            now=self.now,
            active_run=None,
            last_run_started_at=last_run_started_at,
            runs_today=1,
            controller=self.controller,
        )

        forecast = forecast_rule_trigger(
            self.rule,
            decision,
            now=self.now,
            last_run_started_at=last_run_started_at,
            controller=self.controller,
        )

        self.assertIsNotNone(forecast)
        self.assertEqual(forecast.at, datetime(2026, 5, 26, 13, 30, tzinfo=timezone.utc))

    def test_manual_weather_delay_stops_active_rule(self) -> None:
        delayed_controller = ControllerSettings(
            schedule_guard_minutes=30,
            default_cooldown_minutes=120,
            default_max_runs_per_day=3,
            automatic_weather_delay_enabled=False,
            automatic_weather_delay_probability_threshold=60,
            automatic_weather_delay_lookahead_hours=12,
            manual_weather_delay_until=self.now + timedelta(hours=4),
            state_file=Path(".bhyve_state.json"),
        )
        delay_status = build_weather_delay_status(
            delayed_controller,
            build_forecast(self.now, [5, 10, 15]),
            self.now,
        )

        decision = evaluate_weather_delay(
            self.rule,
            active_run={"started_at": self.now.isoformat()},
            delay_status=delay_status,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.action, "stop")
        self.assertEqual(decision.reason, "manual_weather_delay_active")

    def test_automatic_weather_delay_uses_forecast_probability(self) -> None:
        rainy_controller = ControllerSettings(
            schedule_guard_minutes=30,
            default_cooldown_minutes=120,
            default_max_runs_per_day=3,
            automatic_weather_delay_enabled=True,
            automatic_weather_delay_probability_threshold=60,
            automatic_weather_delay_lookahead_hours=6,
            manual_weather_delay_until=None,
            state_file=Path(".bhyve_state.json"),
        )
        forecast = build_forecast(self.now, [25, 40, 80, 55])
        delay_status = build_weather_delay_status(rainy_controller, forecast, self.now)

        self.assertTrue(delay_status.automatic_active)
        self.assertIn("80%", delay_status.detail)

    def test_forecast_next_trigger_uses_manual_delay_end(self) -> None:
        delayed_controller = ControllerSettings(
            schedule_guard_minutes=30,
            default_cooldown_minutes=120,
            default_max_runs_per_day=3,
            automatic_weather_delay_enabled=False,
            automatic_weather_delay_probability_threshold=60,
            automatic_weather_delay_lookahead_hours=12,
            manual_weather_delay_until=self.now + timedelta(hours=2),
            state_file=Path(".bhyve_state.json"),
        )
        forecast = build_forecast(self.now, [5, 10, 15])
        delay_status = build_weather_delay_status(delayed_controller, forecast, self.now)
        decision = evaluate_weather_delay(self.rule, active_run=None, delay_status=delay_status)

        trigger = forecast_rule_trigger(
            self.rule,
            decision,
            now=self.now,
            last_run_started_at=None,
            controller=delayed_controller,
            delay_status=delay_status,
            forecast=forecast,
        )

        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.at, self.now + timedelta(hours=2))

    def test_forecast_next_trigger_uses_first_safe_forecast_hour(self) -> None:
        rainy_controller = ControllerSettings(
            schedule_guard_minutes=30,
            default_cooldown_minutes=120,
            default_max_runs_per_day=3,
            automatic_weather_delay_enabled=True,
            automatic_weather_delay_probability_threshold=60,
            automatic_weather_delay_lookahead_hours=6,
            manual_weather_delay_until=None,
            state_file=Path(".bhyve_state.json"),
        )
        forecast = build_forecast(self.now, [80, 70, 45, 20])
        delay_status = build_weather_delay_status(rainy_controller, forecast, self.now)
        decision = evaluate_weather_delay(self.rule, active_run=None, delay_status=delay_status)

        trigger = forecast_rule_trigger(
            self.rule,
            decision,
            now=self.now,
            last_run_started_at=None,
            controller=rainy_controller,
            delay_status=delay_status,
            forecast=forecast,
        )

        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.at, self.now + timedelta(hours=2))


class ManualWateringRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            path=Path("config.json"),
            bhyve=BhyveSettings(
                email="user@example.com",
                password="secret",
                api_key=None,
                credential_mode="password",
                poll_interval_seconds=300,
                request_timeout_seconds=30,
            ),
            weather=WeatherSettings(
                provider="open_meteo",
                latitude=40.0,
                longitude=-111.0,
                temperature_unit="fahrenheit",
            ),
            controller=ControllerSettings(
                schedule_guard_minutes=30,
                default_cooldown_minutes=120,
                default_max_runs_per_day=3,
                automatic_weather_delay_enabled=False,
                automatic_weather_delay_probability_threshold=60,
                automatic_weather_delay_lookahead_hours=12,
                manual_weather_delay_until=None,
                state_file=Path(".bhyve_state.json"),
            ),
            rules=[],
        )

    async def test_sub_minute_start_uses_one_minute_then_stops(self) -> None:
        service = BhyveTemperatureService(self.config)
        session = Mock()
        session.close = AsyncMock()
        client = Mock()
        client.start_manual_watering = AsyncMock()
        client.stop_manual_watering = AsyncMock()
        service._build_clients = AsyncMock(return_value=(session, client, Mock()))

        with unittest.mock.patch("bhyve_app.controller.asyncio.sleep", new=AsyncMock()) as sleep:
            await service.start_manual_watering(
                "device-1",
                2,
                0.5,
                wait_for_scheduled_stop=True,
            )

        client.start_manual_watering.assert_awaited_once_with("device-1", 2, 1)
        sleep.assert_awaited_once_with(30.0)
        client.stop_manual_watering.assert_awaited_once_with("device-1")


if __name__ == "__main__":
    unittest.main()