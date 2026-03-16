from __future__ import annotations

import importlib.util
import sys
import urllib.request
import json
from typing import Any


class NotificationService:
    """Desktop notifications and webhook alerts for build results.

    Primary: plyer library.  Fallback: terminal bell + print.
    """

    _SECTION = "notification_settings"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _settings(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def set_config(
        self,
        state: dict[str, Any],
        enabled: bool = True,
        webhook_url: str = "",
    ) -> dict[str, Any]:
        cfg = {"enabled": enabled, "webhook_url": webhook_url}
        state[self._SECTION] = cfg
        return cfg

    def get_config(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.get(self._SECTION, {"enabled": False, "webhook_url": ""})

    # --------------------------------------------------------------------- #
    # Notification                                                            #
    # --------------------------------------------------------------------- #

    def notify(
        self,
        title: str,
        message: str,
        success: bool = True,
    ) -> dict[str, Any]:
        sent = False
        method = "none"

        if importlib.util.find_spec("plyer") is not None:
            try:
                from plyer import notification  # type: ignore[import]

                notification.notify(
                    title=title,
                    message=message,
                    app_name="OtterForge",
                    timeout=6,
                )
                sent = True
                method = "plyer"
            except Exception:  # noqa: BLE001
                pass

        if not sent:
            # Fallback: terminal bell + summary
            sys.stdout.write(f"\a[OtterForge] {title}: {message}\n")
            sys.stdout.flush()
            method = "terminal"
            sent = True

        return {"sent": sent, "method": method, "title": title, "success": success}

    def post_webhook(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not url:
            return {"sent": False, "reason": "No webhook URL configured."}

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                status = resp.status
        except Exception as exc:  # noqa: BLE001
            return {"sent": False, "error": str(exc)}

        return {"sent": True, "status": status, "url": url}

    def auto_notify(
        self,
        state: dict[str, Any],
        project_name: str,
        builder_name: str,
        success: bool,
        duration: float,
    ) -> dict[str, Any]:
        """Fire notification + webhook if enabled in state."""
        cfg = self.get_config(state)
        if not cfg.get("enabled"):
            return {"skipped": True, "reason": "Notifications disabled"}

        status_str = "succeeded" if success else "FAILED"
        title = f"Build {status_str}: {project_name}"
        message = f"Builder: {builder_name}  |  Duration: {duration:.1f}s"

        notif_result = self.notify(title, message, success=success)

        webhook_url = cfg.get("webhook_url", "")
        webhook_result = None
        if webhook_url:
            webhook_result = self.post_webhook(
                webhook_url,
                {
                    "project": project_name,
                    "builder": builder_name,
                    "success": success,
                    "duration": duration,
                    "status": status_str,
                },
            )

        return {
            "notification": notif_result,
            "webhook": webhook_result,
        }
