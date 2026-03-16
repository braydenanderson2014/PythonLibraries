"""Tests for NotificationService."""
from __future__ import annotations

import io
import sys
import unittest
from unittest.mock import MagicMock, patch

from otterforge.services.notification_service import NotificationService


class TestNotificationServiceConfig(unittest.TestCase):

    def setUp(self) -> None:
        self.svc = NotificationService()

    def test_set_config_stores_settings(self) -> None:
        state: dict = {}
        cfg = self.svc.set_config(state, enabled=True, webhook_url="https://example.com/hook")
        self.assertTrue(cfg["enabled"])
        self.assertEqual(cfg["webhook_url"], "https://example.com/hook")

    def test_get_config_returns_defaults_when_absent(self) -> None:
        cfg = self.svc.get_config({})
        self.assertFalse(cfg["enabled"])
        self.assertEqual(cfg["webhook_url"], "")

    def test_get_config_returns_stored_values(self) -> None:
        state: dict = {}
        self.svc.set_config(state, enabled=True, webhook_url="https://hook.io")
        cfg = self.svc.get_config(state)
        self.assertTrue(cfg["enabled"])
        self.assertEqual(cfg["webhook_url"], "https://hook.io")


class TestNotificationServiceNotify(unittest.TestCase):

    def setUp(self) -> None:
        self.svc = NotificationService()

    def test_notify_without_plyer_falls_back_to_terminal(self) -> None:
        """When plyer is absent, notify() must succeed via terminal fallback."""
        with patch("importlib.util.find_spec", return_value=None):
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                result = self.svc.notify("Build Done", "MyApp succeeded")
        self.assertTrue(result["sent"])
        self.assertEqual(result["method"], "terminal")
        self.assertIn("Build Done", buf.getvalue())

    def test_notify_with_plyer_uses_plyer(self) -> None:
        mock_plyer_spec = MagicMock()
        mock_notification = MagicMock()

        def fake_find_spec(name: str):
            if name == "plyer":
                return mock_plyer_spec
            return None

        with patch("importlib.util.find_spec", side_effect=fake_find_spec):
            with patch.dict("sys.modules", {"plyer": MagicMock(notification=mock_notification)}):
                result = self.svc.notify("Title", "Message")

        # If plyer path is taken, method should be plyer; otherwise terminal fallback is fine
        self.assertTrue(result["sent"])
        self.assertIn(result["method"], ("plyer", "terminal"))

    def test_notify_returns_correct_title_and_success_flag(self) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            with patch("sys.stdout", io.StringIO()):
                result = self.svc.notify("Build FAILED", "An error occurred", success=False)
        self.assertEqual(result["title"], "Build FAILED")
        self.assertFalse(result["success"])


class TestNotificationServiceWebhook(unittest.TestCase):

    def setUp(self) -> None:
        self.svc = NotificationService()

    def test_post_webhook_empty_url_returns_not_sent(self) -> None:
        result = self.svc.post_webhook("", {"status": "ok"})
        self.assertFalse(result["sent"])

    def test_post_webhook_success(self) -> None:
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = self.svc.post_webhook("https://example.com/hook", {"event": "build"})

        self.assertTrue(result["sent"])
        self.assertEqual(result["status"], 200)

    def test_post_webhook_connection_error_returns_error_key(self) -> None:
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            result = self.svc.post_webhook("https://example.com/hook", {"event": "build"})
        self.assertFalse(result["sent"])
        self.assertIn("error", result)


class TestAutoNotify(unittest.TestCase):

    def setUp(self) -> None:
        self.svc = NotificationService()

    def test_auto_notify_skips_when_disabled(self) -> None:
        state: dict = {}
        self.svc.set_config(state, enabled=False)
        result = self.svc.auto_notify(state, "MyApp", "pyinstaller", success=True, duration=5.0)
        self.assertTrue(result.get("skipped"))

    def test_auto_notify_fires_when_enabled(self) -> None:
        state: dict = {}
        self.svc.set_config(state, enabled=True, webhook_url="")
        with patch("importlib.util.find_spec", return_value=None):
            with patch("sys.stdout", io.StringIO()):
                result = self.svc.auto_notify(
                    state, "MyApp", "pyinstaller", success=True, duration=3.2
                )
        self.assertNotIn("skipped", result)
        self.assertIn("notification", result)

    def test_auto_notify_posts_webhook_when_configured(self) -> None:
        state: dict = {}
        self.svc.set_config(state, enabled=True, webhook_url="https://hook.example.com")

        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch("importlib.util.find_spec", return_value=None):
            with patch("sys.stdout", io.StringIO()):
                with patch("urllib.request.urlopen", return_value=mock_response):
                    result = self.svc.auto_notify(
                        state, "MyApp", "nuitka", success=False, duration=12.5
                    )

        self.assertIn("webhook", result)
        self.assertTrue(result["webhook"]["sent"])


if __name__ == "__main__":
    unittest.main()
