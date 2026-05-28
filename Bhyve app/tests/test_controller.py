from __future__ import annotations

from unittest.mock import AsyncMock, Mock
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from bhyve_app.config import AppConfig, BhyveSettings, ControllerSettings, DevicePolicy, ScheduleRule, TemperatureRule, WeatherSettings
from bhyve_app.controller import (
    BhyveTemperatureService,
    build_weather_delay_status,
    evaluate_weather_delay,
    evaluate_rule,
    evaluate_schedule_rule,
    forecast_rule_trigger,
    next_schedule_trigger,
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

    def test_windy_conditions_block_start(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            sensor_reading={"wind_speed_mph": 20},
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "windy_conditions_active")

    def test_soil_moisture_blocks_start(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=92,
            sensor_reading={"soil_moisture_percent": 40},
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "soil_moisture_sufficient")

    def test_cloudy_conditions_block_start(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=89,
            sensor_reading={"cloud_cover_percent": 90},
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "cloudy_conditions_active")

    def test_sensor_temperature_override_can_trigger_start(self) -> None:
        decision = evaluate_rule(
            self.rule,
            build_device(),
            temperature=75,
            sensor_reading={"temperature": 92},
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

    def test_does_not_block_on_stale_watering_status_without_current_station(self) -> None:
        # Bhyve API can return a non-null watering_status dict with no current_station
        # when a previous cycle ended but the field wasn't cleared. The rule should
        # proceed normally rather than waiting for the device to finish watering.
        decision = evaluate_rule(
            self.rule,
            build_device(watering_status={"status": "idle"}),
            temperature=92,
            now=self.now,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertNotEqual(decision.reason, "device_busy_with_existing_watering")
        self.assertEqual(decision.action, "start")

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
            temperature=92,
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
            temperature=92,
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
            temperature=92,
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
            temperature=92,
            last_run_started_at=None,
            controller=rainy_controller,
            delay_status=delay_status,
            forecast=forecast,
        )

        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.at, self.now + timedelta(hours=2))

    def test_cooldown_range_picks_shorter_wait_when_hotter(self) -> None:
        hot_rule = TemperatureRule(
            name="Heat boost",
            device_id="device-1",
            station=1,
            start_above=90,
            stop_below=80,
            manual_run_minutes=10,
            enabled=True,
            max_runs_per_day=2,
            cooldown_minutes=None,
            allowed_hours_local=(10, 19),
            cooldown_minutes_range=(60, 180),
        )

        decision = evaluate_rule(
            hot_rule,
            build_device(),
            temperature=100,
            now=self.now,
            active_run=None,
            last_run_started_at=self.now - timedelta(minutes=75),
            runs_today=1,
            controller=self.controller,
        )

        self.assertEqual(decision.action, "start")
        self.assertEqual(decision.reason, "temperature_above_start_threshold")

    def test_cooldown_range_picks_longer_wait_when_cooler(self) -> None:
        hot_rule = TemperatureRule(
            name="Heat boost",
            device_id="device-1",
            station=1,
            start_above=90,
            stop_below=80,
            manual_run_minutes=10,
            enabled=True,
            max_runs_per_day=2,
            cooldown_minutes=None,
            allowed_hours_local=(10, 19),
            cooldown_minutes_range=(60, 180),
        )

        decision = evaluate_rule(
            hot_rule,
            build_device(),
            temperature=91,
            now=self.now,
            active_run=None,
            last_run_started_at=self.now - timedelta(minutes=75),
            runs_today=1,
            controller=self.controller,
        )

        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "cooldown_active")


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

    async def test_external_watering_is_stopped_when_rule_requests_it(self) -> None:
        rule = TemperatureRule(
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
            stop_external_watering=True,
        )
        config = AppConfig(
            path=Path("config.json"),
            bhyve=self.config.bhyve,
            weather=self.config.weather,
            controller=self.config.controller,
            rules=[rule],
        )
        service = BhyveTemperatureService(config)
        session = Mock()
        session.close = AsyncMock()
        bhyve_client = Mock()
        bhyve_client.get_devices = AsyncMock(
            return_value=[build_device(watering_status={"current_station": 1})]
        )
        bhyve_client.stop_manual_watering = AsyncMock()
        weather_client = Mock()
        now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
        snapshot = Mock()
        snapshot.temperature = Mock(value=92, unit="fahrenheit", observed_at=now)
        snapshot.forecast = build_forecast(now, [0])
        weather_client.get_weather_snapshot = AsyncMock(return_value=snapshot)
        service._build_clients = AsyncMock(return_value=(session, bhyve_client, weather_client))

        report = await service.run_cycle(apply_changes=True)

        bhyve_client.stop_manual_watering.assert_awaited_once_with("device-1")
        self.assertEqual(report.decisions[0].reason, "external_watering_auto_stopped")

    async def test_stop_external_watering_fires_when_stale_active_run_present(self) -> None:
        """A stale active_run from a previous controller cycle must not block stop_external_watering."""
        import dataclasses

        with tempfile.TemporaryDirectory() as temp_dir:
            rule = TemperatureRule(
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
                stop_external_watering=True,
            )
            controller_cfg = dataclasses.replace(
                self.config.controller,
                state_file=Path(temp_dir) / "state.json",
            )
            config = AppConfig(
                path=Path("config.json"),
                bhyve=self.config.bhyve,
                weather=self.config.weather,
                controller=controller_cfg,
                rules=[rule],
            )
            service = BhyveTemperatureService(config)

            # Simulate a stale active_run from a previous controller cycle: ran station 1
            # for 10 minutes, started 2 hours ago — long overdue but state was never cleared.
            stale_started_at = datetime(2026, 5, 26, 10, 0, tzinfo=timezone.utc)
            service._state.set_active_run(
                "device-1",
                1,
                rule_name="Heat boost",
                started_at=stale_started_at,
                requested_minutes=10,
                trigger_temperature=92.0,
            )

            session = Mock()
            session.close = AsyncMock()
            bhyve_client = Mock()
            # BHyve timer is now running station 1 (not the controller).
            bhyve_client.get_devices = AsyncMock(
                return_value=[build_device(watering_status={"current_station": 1})]
            )
            bhyve_client.stop_manual_watering = AsyncMock()
            weather_client = Mock()
            # "now" is 2 hours after stale_started_at — well past the 10 min run + 2 min grace.
            now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
            snapshot = Mock()
            snapshot.temperature = Mock(value=92, unit="fahrenheit", observed_at=now)
            snapshot.forecast = build_forecast(now, [0])
            weather_client.get_weather_snapshot = AsyncMock(return_value=snapshot)
            service._build_clients = AsyncMock(return_value=(session, bhyve_client, weather_client))

            report = await service.run_cycle(apply_changes=True)

            bhyve_client.stop_manual_watering.assert_awaited_once_with("device-1")
            self.assertEqual(report.decisions[0].reason, "external_watering_auto_stopped")

    async def test_block_unlisted_stations_stops_unapproved_station(self) -> None:
        """When block_unlisted_stations is True, any station with no rule is stopped."""
        # device-1: restricted device, only station 1 has a rule.
        # The timer fires station 2 (no rule) — it must be stopped.
        rule = TemperatureRule(
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
            stop_external_watering=False,
        )
        config = AppConfig(
            path=Path("config.json"),
            bhyve=self.config.bhyve,
            weather=self.config.weather,
            controller=self.config.controller,
            rules=[rule],
            device_policies=[DevicePolicy(device_id="device-1", block_unlisted_stations=True)],
        )
        service = BhyveTemperatureService(config)
        session = Mock()
        session.close = AsyncMock()
        bhyve_client = Mock()
        # Timer is running station 2, which has no rule.
        bhyve_client.get_devices = AsyncMock(
            return_value=[{
                "id": "device-1",
                "status": {"watering_status": {"current_station": 2}, "next_start_time": None},
            }]
        )
        bhyve_client.stop_manual_watering = AsyncMock()
        weather_client = Mock()
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        snapshot = Mock()
        snapshot.temperature = Mock(value=70, unit="fahrenheit", observed_at=now)
        snapshot.forecast = build_forecast(now, [0])
        weather_client.get_weather_snapshot = AsyncMock(return_value=snapshot)
        service._build_clients = AsyncMock(return_value=(session, bhyve_client, weather_client))

        report = await service.run_cycle(apply_changes=True)

        bhyve_client.stop_manual_watering.assert_awaited_once_with("device-1")
        blocked = [d for d in report.decisions if d.reason == "unlisted_station_blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0].station, 2)

    async def test_block_unlisted_stations_stops_timer_on_ruled_station(self) -> None:
        """When block_unlisted_stations is True, a timer-initiated run on a ruled station is
        still stopped — the controller did not start it, so it should not be running."""
        rule = TemperatureRule(
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
            stop_external_watering=False,
        )
        config = AppConfig(
            path=Path("config.json"),
            bhyve=self.config.bhyve,
            weather=self.config.weather,
            controller=self.config.controller,
            rules=[rule],
            device_policies=[DevicePolicy(device_id="device-1", block_unlisted_stations=True)],
        )
        service = BhyveTemperatureService(config)
        session = Mock()
        session.close = AsyncMock()
        bhyve_client = Mock()
        # BHyve timer running station 1 — controller did not start this run.
        bhyve_client.get_devices = AsyncMock(
            return_value=[{
                "id": "device-1",
                "status": {"watering_status": {"current_station": 1}, "next_start_time": None},
            }]
        )
        bhyve_client.stop_manual_watering = AsyncMock()
        weather_client = Mock()
        now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        snapshot = Mock()
        snapshot.temperature = Mock(value=70, unit="fahrenheit", observed_at=now)
        snapshot.forecast = build_forecast(now, [0])
        weather_client.get_weather_snapshot = AsyncMock(return_value=snapshot)
        service._build_clients = AsyncMock(return_value=(session, bhyve_client, weather_client))

        report = await service.run_cycle(apply_changes=True)

        # Block logic must stop the timer run because the controller didn't initiate it.
        bhyve_client.stop_manual_watering.assert_awaited_once_with("device-1")
        blocked = [d for d in report.decisions if d.reason == "unlisted_station_blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0].station, 1)

    async def test_motion_detection_pauses_and_stops_watering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            rule = TemperatureRule(
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
                pause_on_motion=True,
                motion_pause_minutes=15,
            )
            config = AppConfig(
                path=Path("config.json"),
                bhyve=self.config.bhyve,
                weather=self.config.weather,
                controller=ControllerSettings(
                    schedule_guard_minutes=30,
                    default_cooldown_minutes=120,
                    default_max_runs_per_day=3,
                    automatic_weather_delay_enabled=False,
                    automatic_weather_delay_probability_threshold=60,
                    automatic_weather_delay_lookahead_hours=12,
                    manual_weather_delay_until=None,
                    state_file=Path(temp_dir) / "state.json",
                ),
                rules=[rule],
            )
            service = BhyveTemperatureService(config)
            session = Mock()
            session.close = AsyncMock()
            bhyve_client = Mock()
            bhyve_client.get_devices = AsyncMock(
                return_value=[build_device(watering_status={"current_station": 1})]
            )
            bhyve_client.stop_manual_watering = AsyncMock()
            weather_client = Mock()
            now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
            snapshot = Mock()
            snapshot.temperature = Mock(value=92, unit="fahrenheit", observed_at=now)
            snapshot.forecast = build_forecast(now, [0])
            weather_client.get_weather_snapshot = AsyncMock(return_value=snapshot)
            service._build_clients = AsyncMock(return_value=(session, bhyve_client, weather_client))

            service.record_sensor_reading(
                device_id="device-1",
                station=1,
                reading={"motion_detected": True, "observed_at": now.isoformat(), "source": "esp32"},
            )

            report = await service.run_cycle(apply_changes=True)
            self.assertEqual(report.decisions[0].reason, "motion_pause_active")
            self.assertEqual(report.decisions[0].action, "stop")
            self.assertIsNotNone(report.decisions[0].pause_remaining_seconds)
            bhyve_client.stop_manual_watering.assert_awaited_once_with("device-1")

            bhyve_client.stop_manual_watering.reset_mock()
            bhyve_client.get_devices = AsyncMock(return_value=[build_device()])

            report = await service.run_cycle(apply_changes=True)
            self.assertEqual(report.decisions[0].reason, "motion_pause_active")
            self.assertEqual(report.decisions[0].action, "noop")
            bhyve_client.stop_manual_watering.assert_not_called()


class EvaluateScheduleRuleTests(unittest.TestCase):
    """Tests for evaluate_schedule_rule."""

    def setUp(self) -> None:
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
        # Monday 2026-05-25 06:01 UTC — inside the 06:00 window (within 5 min).
        self.now_in_window = datetime(2026, 5, 25, 6, 1, tzinfo=timezone.utc)
        self.rule = ScheduleRule(
            name="Morning Run",
            device_id="device-1",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[0, 1, 2, 3, 4],  # Mon–Fri
            enabled=True,
        )

    def test_fires_in_window(self) -> None:
        decision = evaluate_schedule_rule(
            self.rule,
            build_device(),
            temperature=65,
            now=self.now_in_window,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "start")
        self.assertEqual(decision.reason, "scheduled_time_triggered")

    def test_skips_wrong_day(self) -> None:
        # Saturday = weekday 5, not in schedule_days (Mon–Fri).
        saturday = datetime(2026, 5, 30, 6, 1, tzinfo=timezone.utc)
        decision = evaluate_schedule_rule(
            self.rule,
            build_device(),
            temperature=65,
            now=saturday,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "not_a_scheduled_day")

    def test_skips_outside_window(self) -> None:
        # 6:06 — 6 minutes after window start (window is 5 minutes).
        after_window = datetime(2026, 5, 25, 6, 6, tzinfo=timezone.utc)
        decision = evaluate_schedule_rule(
            self.rule,
            build_device(),
            temperature=65,
            now=after_window,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "outside_schedule_window")

    def test_skips_below_min_temperature(self) -> None:
        rule = ScheduleRule(
            name="Warm Only",
            device_id="device-1",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[],
            enabled=True,
            min_temperature=50.0,
        )
        decision = evaluate_schedule_rule(
            rule,
            build_device(),
            temperature=40.0,
            now=self.now_in_window,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "temperature_below_minimum")

    def test_respects_cooldown(self) -> None:
        # Last run was 30 min ago; rule has a 60-minute cooldown.
        rule = ScheduleRule(
            name="Cooldown Rule",
            device_id="device-1",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[],
            enabled=True,
            cooldown_minutes=60,
        )
        last_run = self.now_in_window - timedelta(minutes=30)
        decision = evaluate_schedule_rule(
            rule,
            build_device(),
            temperature=65,
            now=self.now_in_window,
            active_run=None,
            last_run_started_at=last_run,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "cooldown_active")

    def test_disabled_rule_is_noop(self) -> None:
        rule = ScheduleRule(
            name="Disabled",
            device_id="device-1",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[],
            enabled=False,
        )
        decision = evaluate_schedule_rule(
            rule,
            build_device(),
            temperature=65,
            now=self.now_in_window,
            active_run=None,
            last_run_started_at=None,
            runs_today=0,
            controller=self.controller,
        )
        self.assertEqual(decision.action, "noop")
        self.assertEqual(decision.reason, "rule_disabled")


class NextScheduleTriggerTests(unittest.TestCase):
    """Tests for next_schedule_trigger."""

    def test_finds_next_time_same_day(self) -> None:
        rule = ScheduleRule(
            name="r",
            device_id="d",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(18, 0)],
            schedule_days=[],
            enabled=True,
        )
        now = datetime(2026, 5, 25, 6, 0, tzinfo=timezone.utc)
        result = next_schedule_trigger(rule, now)
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 18)
        self.assertEqual(result.date(), now.date())

    def test_wraps_to_next_day(self) -> None:
        rule = ScheduleRule(
            name="r",
            device_id="d",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[],
            enabled=True,
        )
        now = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
        result = next_schedule_trigger(rule, now)
        self.assertIsNotNone(result)
        self.assertEqual(result.day, 26)

    def test_skips_days_not_in_schedule_days(self) -> None:
        # schedule_days = [0] (Monday only). Now is Monday 06:01, so next is next Monday.
        rule = ScheduleRule(
            name="r",
            device_id="d",
            station=1,
            manual_run_minutes=10,
            schedule_times=[(6, 0)],
            schedule_days=[0],
            enabled=True,
        )
        # Monday 2026-05-25 08:00 — after the window.
        now = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
        result = next_schedule_trigger(rule, now)
        self.assertIsNotNone(result)
        self.assertEqual(result.weekday(), 0)  # Monday
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 1)  # Next Monday = June 1

    def test_returns_none_when_no_times(self) -> None:
        rule = ScheduleRule(
            name="r",
            device_id="d",
            station=1,
            manual_run_minutes=10,
            schedule_times=[],
            schedule_days=[],
            enabled=True,
        )
        result = next_schedule_trigger(rule, datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()