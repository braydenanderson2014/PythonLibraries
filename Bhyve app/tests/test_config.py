from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bhyve_app.config import (
    default_config_template,
    load_raw_config,
    looks_like_env_var_name,
    parse_app_config,
    save_raw_config,
)


class ConfigHelpersTests(unittest.TestCase):
    def test_missing_config_returns_default_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = load_raw_config(config_path)

        self.assertEqual(config["bhyve"]["password_env"], "BHYVE_PASSWORD")
        self.assertEqual(config["rules"][0]["station"], 1)

    def test_save_and_reload_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)

            save_raw_config(config_path, config)
            reloaded = load_raw_config(config_path)

        self.assertEqual(reloaded["bhyve"]["email"], "user@example.com")
        self.assertEqual(reloaded["bhyve"]["password"], "secret")

    def test_parse_raw_config_uses_literal_password(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)

            parsed = parse_app_config(config, config_path)

        self.assertEqual(parsed.bhyve.email, "user@example.com")
        self.assertEqual(parsed.bhyve.password, "secret")

    def test_parse_raw_config_accepts_legacy_password_saved_in_password_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"].pop("password", None)
            config["bhyve"]["password_env"] = "secret!not_an_env_var"

            parsed = parse_app_config(config, config_path)

        self.assertEqual(parsed.bhyve.password, "secret!not_an_env_var")

    def test_looks_like_env_var_name(self) -> None:
        self.assertTrue(looks_like_env_var_name("BHYVE_PASSWORD"))
        self.assertFalse(looks_like_env_var_name("secret!not_an_env_var"))

    def test_parse_raw_config_supports_api_key_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["credential_mode"] = "token"
            config["bhyve"]["api_key"] = "token-123"
            config["bhyve"].pop("password_env", None)

            parsed = parse_app_config(config, config_path)

        self.assertEqual(parsed.bhyve.api_key, "token-123")
        self.assertEqual(parsed.bhyve.credential_mode, "token")
        self.assertIsNone(parsed.bhyve.password)

    def test_parse_raw_config_supports_fractional_manual_run_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["rules"][0]["manual_run_minutes"] = 0.5

            parsed = parse_app_config(config, config_path)

        self.assertEqual(parsed.rules[0].manual_run_minutes, 0.5)

    def test_parse_raw_config_supports_weather_delay_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["controller"]["automatic_weather_delay_enabled"] = True
            config["controller"]["automatic_weather_delay_probability_threshold"] = 70
            config["controller"]["automatic_weather_delay_lookahead_hours"] = 6
            config["controller"]["manual_weather_delay_until"] = "2026-05-27T12:00:00+00:00"

            parsed = parse_app_config(config, config_path)

        self.assertTrue(parsed.controller.automatic_weather_delay_enabled)
        self.assertEqual(parsed.controller.automatic_weather_delay_probability_threshold, 70)
        self.assertEqual(parsed.controller.automatic_weather_delay_lookahead_hours, 6)
        self.assertEqual(
            parsed.controller.manual_weather_delay_until,
            datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        )

    def test_parse_raw_config_supports_cooldown_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["rules"][0]["cooldown_minutes"] = None
            config["rules"][0]["cooldown_minutes_range"] = [60, 180]

            parsed = parse_app_config(config, config_path)

        self.assertEqual(parsed.rules[0].cooldown_minutes_range, (60, 180))

    def test_parse_raw_config_supports_stop_external_watering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["rules"][0]["stop_external_watering"] = True
            config["rules"][0]["pause_on_motion"] = True
            config["rules"][0]["motion_pause_minutes"] = 12

            parsed = parse_app_config(config, config_path)

        self.assertTrue(parsed.rules[0].stop_external_watering)
        self.assertTrue(parsed.rules[0].pause_on_motion)
        self.assertEqual(parsed.rules[0].motion_pause_minutes, 12)

    def test_parse_raw_config_rejects_invalid_cooldown_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["rules"][0]["cooldown_minutes_range"] = [180, 60]

            with self.assertRaises(ValueError):
                parse_app_config(config, config_path)

    def test_parse_raw_config_supports_ingest_transports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = default_config_template()
            config["bhyve"]["email"] = "user@example.com"
            config["bhyve"]["password"] = "secret"
            config["bhyve"].pop("password_env", None)
            config["ingest"]["serial"] = {
                "enabled": True,
                "port": "COM7",
                "baudrate": 57600,
                "read_timeout_seconds": 2,
                "reconnect_seconds": 9,
            }
            config["ingest"]["bluetooth"] = {
                "enabled": True,
                "address": "AA:BB:CC:DD:EE:FF",
                "characteristic_uuid": "12345678-1234-5678-1234-56789abcdef0",
                "reconnect_seconds": 7,
            }

            parsed = parse_app_config(config, config_path)

        self.assertTrue(parsed.ingest.serial.enabled)
        self.assertEqual(parsed.ingest.serial.port, "COM7")
        self.assertEqual(parsed.ingest.serial.baudrate, 57600)
        self.assertTrue(parsed.ingest.bluetooth.enabled)
        self.assertEqual(parsed.ingest.bluetooth.address, "AA:BB:CC:DD:EE:FF")


if __name__ == "__main__":
    unittest.main()