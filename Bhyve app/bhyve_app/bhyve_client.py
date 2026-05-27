from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientResponseError, ClientSession, ClientTimeout, WSMsgType

API_HOST = "https://api.orbitbhyve.com"
WEB_HOST = "https://techsupport.orbitbhyve.com"
WS_HOST = "wss://api.orbitbhyve.com/v1/events"

LOGIN_PATH = "/v1/session"
DEVICES_PATH = "/v1/devices"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)

LOGGER = logging.getLogger(__name__)


class BhyveClientError(RuntimeError):
    """Raised when the Orbit BHyve API request fails."""


class AuthenticationError(BhyveClientError):
    """Raised when Orbit BHyve rejects credentials or tokens."""


class BhyveClient:
    def __init__(
        self,
        email: str | None,
        password: str | None,
        session: ClientSession,
        api_key: str | None = None,
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._api_key = api_key
        self._token: str | None = None

    @staticmethod
    def build_timeout(total_seconds: int) -> ClientTimeout:
        return ClientTimeout(total=total_seconds)

    async def login(self) -> None:
        if self._token:
            return

        if self._api_key:
            self._token = self._api_key
            return

        if not self._email or not self._password:
            raise AuthenticationError(
                "Orbit BHyve login requires either email/password or an Orbit API token"
            )

        payload = {"session": {"email": self._email, "password": self._password}}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": WEB_HOST,
            "Referer": f"{WEB_HOST}/",
            "User-Agent": USER_AGENT,
            "orbit-app-id": "Bhyve Dashboard",
            "orbit-api-key": "null",
        }
        url = f"{API_HOST}{LOGIN_PATH}"

        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except ClientResponseError as exc:
            if exc.status in {401, 403}:
                raise AuthenticationError("Orbit BHyve rejected the credentials") from exc
            raise BhyveClientError(f"BHyve login failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise BhyveClientError(f"BHyve login failed: {exc}") from exc

        token = data.get("orbit_api_key") or data.get("orbit_session_token")
        if not token:
            raise AuthenticationError("Orbit BHyve did not return a session token")
        self._token = str(token)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json; charset=utf-8;",
            "Origin": WEB_HOST,
            "Referer": f"{WEB_HOST}/",
            "User-Agent": USER_AGENT,
            "orbit-app-id": "Bhyve Dashboard",
            "orbit-api-key": self._token or "null",
            "Orbit-Session-Token": self._token or "",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        await self.login()
        url = f"{API_HOST}{path}"
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=self._auth_headers(),
            ) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except ClientResponseError as exc:
            if exc.status in {401, 403}:
                self._token = None
                raise AuthenticationError("BHyve request was not authorized") from exc
            raise BhyveClientError(f"BHyve request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise BhyveClientError(f"BHyve request failed: {exc}") from exc

    async def get_devices(self) -> list[dict[str, Any]]:
        devices = await self._request("GET", DEVICES_PATH)
        if not isinstance(devices, list):
            raise BhyveClientError("BHyve devices response was not a list")
        return devices

    async def get_device(self, device_id: str) -> dict[str, Any] | None:
        for device in await self.get_devices():
            if str(device.get("id")) == str(device_id):
                return device
        return None

    async def send_message(self, payload: dict[str, Any]) -> None:
        await self.login()
        if not self._token:
            raise AuthenticationError("Cannot send websocket message without a token")

        async with self._session.ws_connect(
            WS_HOST,
            origin=WEB_HOST,
            headers={"User-Agent": USER_AGENT},
            heartbeat=25,
        ) as websocket:
            await websocket.send_str(
                json.dumps(
                    {
                        "event": "app_connection",
                        "orbit_session_token": self._token,
                    }
                )
            )

            try:
                message = await websocket.receive(timeout=3)
                if message.type == WSMsgType.TEXT:
                    LOGGER.debug("BHyve auth response: %s", message.data)
            except asyncio.TimeoutError:
                LOGGER.debug("BHyve websocket auth ack timed out")

            await websocket.send_str(json.dumps(payload))

            try:
                message = await websocket.receive(timeout=3)
                if message.type == WSMsgType.TEXT:
                    LOGGER.debug("BHyve websocket response: %s", message.data)
            except asyncio.TimeoutError:
                LOGGER.debug("BHyve websocket response timed out")

    async def start_manual_watering(
        self,
        device_id: str,
        station: int,
        minutes: int,
    ) -> None:
        payload = {
            "event": "change_mode",
            "mode": "manual",
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stations": [{"station": int(station), "run_time": int(minutes)}],
        }
        await self.send_message(payload)

    async def stop_manual_watering(self, device_id: str) -> None:
        payload = {
            "event": "change_mode",
            "mode": "manual",
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stations": [],
        }
        await self.send_message(payload)

    async def set_manual_preset_runtime(self, device_id: str, minutes: int) -> None:
        payload = {
            "event": "set_manual_preset_runtime",
            "device_id": device_id,
            "seconds": int(minutes) * 60,
        }
        await self.send_message(payload)
