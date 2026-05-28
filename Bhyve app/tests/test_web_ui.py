from __future__ import annotations

import unittest
from datetime import datetime, timezone

from bhyve_app.config import default_config_template
from bhyve_app.web_ui import (
    _json_safe,
    _parse_sensor_bool,
    _parse_sensor_message,
    _parse_sensor_number,
    merge_ui_config,
    sanitize_config_for_ui,
)


class WebUiConfigHelpersTests(unittest.TestCase):
    def test_json_safe_serializes_datetime_values(self) -> None:
        observed_at = datetime(2026, 5, 26, 19, 45, tzinfo=timezone.utc)

        payload = _json_safe({"temperature": {"observed_at": observed_at}})

        self.assertEqual(payload["temperature"]["observed_at"], observed_at.isoformat())

    def test_sanitize_hides_saved_password(self) -> None:
        raw_config = default_config_template()
        raw_config["bhyve"]["password"] = "secret"
        raw_config["bhyve"].pop("password_env", None)

        payload = sanitize_config_for_ui(raw_config)

        self.assertEqual(payload["config"]["bhyve"]["password"], "")
        self.assertTrue(payload["meta"]["has_saved_password"])
        self.assertEqual(payload["meta"]["credential_mode"], "password")
        self.assertEqual(payload["config"]["bhyve"]["password_env"], "")

    def test_sanitize_legacy_password_env_marks_password_mode(self) -> None:
        raw_config = default_config_template()
        raw_config["bhyve"].pop("password", None)
        raw_config["bhyve"]["password_env"] = "secret!not_an_env_var"

        payload = sanitize_config_for_ui(raw_config)

        self.assertEqual(payload["meta"]["credential_mode"], "password")
        self.assertTrue(payload["meta"]["legacy_password_in_env"])
        self.assertEqual(payload["config"]["bhyve"]["password_env"], "")

    def test_merge_preserves_existing_password_when_left_blank(self) -> None:
        existing = default_config_template()
        existing["bhyve"]["password"] = "secret"
        existing["bhyve"].pop("password_env", None)

        incoming = default_config_template()
        incoming["bhyve"]["email"] = "new@example.com"
        incoming["bhyve"]["credential_mode"] = "password"
        incoming["bhyve"]["password"] = ""
        incoming["bhyve"]["password_env"] = ""

        merged = merge_ui_config(existing, incoming)

        self.assertEqual(merged["bhyve"]["email"], "new@example.com")
        self.assertEqual(merged["bhyve"]["password"], "secret")
        self.assertNotIn("password_env", merged["bhyve"])

    def test_merge_prefers_password_env_when_supplied(self) -> None:
        incoming = default_config_template()
        incoming["bhyve"]["credential_mode"] = "env"
        incoming["bhyve"]["password"] = ""
        incoming["bhyve"]["password_env"] = "BHYVE_PASSWORD"

        merged = merge_ui_config({}, incoming)

        self.assertEqual(merged["bhyve"]["password_env"], "BHYVE_PASSWORD")
        self.assertNotIn("password", merged["bhyve"])

    def test_sanitize_hides_saved_api_key(self) -> None:
        raw_config = default_config_template()
        raw_config["bhyve"]["credential_mode"] = "token"
        raw_config["bhyve"]["api_key"] = "token-123"
        raw_config["bhyve"].pop("password_env", None)

        payload = sanitize_config_for_ui(raw_config)

        self.assertEqual(payload["meta"]["credential_mode"], "token")
        self.assertTrue(payload["meta"]["has_saved_api_key"])
        self.assertEqual(payload["config"]["bhyve"]["api_key"], "")

    def test_merge_preserves_existing_api_key_when_left_blank(self) -> None:
        existing = default_config_template()
        existing["bhyve"]["credential_mode"] = "token"
        existing["bhyve"]["api_key"] = "token-123"
        existing["bhyve"].pop("password_env", None)

        incoming = default_config_template()
        incoming["bhyve"]["credential_mode"] = "token"
        incoming["bhyve"]["api_key"] = ""
        incoming["bhyve"]["password_env"] = ""

        merged = merge_ui_config(existing, incoming)

        self.assertEqual(merged["bhyve"]["api_key"], "token-123")
        self.assertNotIn("password", merged["bhyve"])

    def test_merge_fixes_existing_legacy_password_env_when_using_password_mode(self) -> None:
        existing = default_config_template()
        existing["bhyve"].pop("password", None)
        existing["bhyve"]["password_env"] = "secret!not_an_env_var"

        incoming = default_config_template()
        incoming["bhyve"]["credential_mode"] = "password"
        incoming["bhyve"]["password"] = ""
        incoming["bhyve"]["password_env"] = ""

        merged = merge_ui_config(existing, incoming)

        self.assertEqual(merged["bhyve"]["password"], "secret!not_an_env_var")
        self.assertNotIn("password_env", merged["bhyve"])

    def test_parse_sensor_number_accepts_formatted_values(self) -> None:
        self.assertEqual(_parse_sensor_number("82* F"), 82.0)
        self.assertEqual(_parse_sensor_number("62%"), 62.0)
        self.assertEqual(_parse_sensor_number("15 mph"), 15.0)

    def test_parse_sensor_bool_accepts_motion_values(self) -> None:
        self.assertTrue(_parse_sensor_bool("motion detected"))
        self.assertTrue(_parse_sensor_bool("yes"))
        self.assertFalse(_parse_sensor_bool("clear"))

    def test_parse_sensor_message_accepts_json_object(self) -> None:
        payload = _parse_sensor_message('{"temperature": 78, "humidity": 41}')
        self.assertEqual(payload["temperature"], 78)
        self.assertEqual(payload["humidity"], 41)

    def test_parse_sensor_message_rejects_non_object(self) -> None:
        with self.assertRaises(ValueError):
            _parse_sensor_message('[1, 2, 3]')


if __name__ == "__main__":
    unittest.main()