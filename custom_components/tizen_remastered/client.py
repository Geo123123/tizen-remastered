"""Samsung Tizen client helpers."""

from __future__ import annotations

import base64
import json
import socket
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import websocket
from wakeonlan import send_magic_packet

from .const import DEFAULT_WS_TIMEOUT


class TizenRemasteredError(Exception):
    """Base error for the Tizen Remastered client."""


class TizenRemasteredConnectionError(TizenRemasteredError):
    """Raised when the TV cannot be reached."""


@dataclass(slots=True)
class TVStatus:
    """Current TV status."""

    is_on: bool
    friendly_name: str | None = None
    model: str | None = None
    device_name: str | None = None
    os: str | None = None
    apps: dict[str, str] | None = None


class SamsungTizenClient:
    """Small sync client for Samsung Tizen TVs."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float,
        ws_name: str,
        mac: str | None = None,
        token_path: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._ws_name = ws_name
        self._mac = mac
        self._token_path = Path(token_path) if token_path else None
        self._token: str | None = self._load_token()

    def get_status(self) -> TVStatus:
        """Fetch the current TV status over the local HTTP API."""
        url = f"http://{self._host}:8001/api/v2/"

        try:
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as err:
            return TVStatus(is_on=False)

        data = response.json()
        device = data.get("device", {})

        return TVStatus(
            is_on=True,
            friendly_name=device.get("friendlyName"),
            model=device.get("modelName"),
            device_name=device.get("name"),
            os=device.get("OS"),
        )

    def send_key(self, key: str) -> None:
        """Send a remote key to the TV."""
        connection = self._create_ws_connection()
        payload = {
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey",
            },
        }

        try:
            connection.send(json.dumps(payload))
        except OSError as err:
            raise TizenRemasteredConnectionError(str(err)) from err
        finally:
            connection.close()

    def launch_app(self, app_id: str) -> None:
        """Launch a TV application using the websocket app launcher."""
        connection = self._create_ws_connection()
        payload = {
            "method": "ms.channel.emit",
            "params": {
                "event": "ed.apps.launch",
                "to": "host",
                "data": {
                    "appId": app_id,
                    "action_type": "DEEP_LINK",
                },
            },
        }

        try:
            connection.send(json.dumps(payload))
        except OSError as err:
            raise TizenRemasteredConnectionError(str(err)) from err
        finally:
            connection.close()

    def open_browser(self, url: str) -> None:
        """Open a URL in the TV browser."""
        connection = self._create_ws_connection()
        payload = {
            "method": "ms.channel.emit",
            "params": {
                "event": "ed.apps.launch",
                "to": "host",
                "data": {
                    "appId": "org.tizen.browser",
                    "action_type": "NATIVE_LAUNCH",
                    "metaTag": url,
                },
            },
        }

        try:
            connection.send(json.dumps(payload))
        except OSError as err:
            raise TizenRemasteredConnectionError(str(err)) from err
        finally:
            connection.close()

    def turn_on(self) -> None:
        """Turn on the TV with Wake-on-LAN if a MAC address is configured."""
        if not self._mac:
            raise TizenRemasteredError("No MAC address configured for Wake-on-LAN")
        send_magic_packet(self._mac)

    def _create_ws_connection(self) -> websocket.WebSocket:
        return self._create_ws_connection_inner(allow_token_reset=True)

    def _create_ws_connection_inner(self, allow_token_reset: bool) -> websocket.WebSocket:
        """Create a websocket connection and retry once without a stale token."""
        encoded_name = base64.b64encode(self._ws_name.encode("utf-8")).decode("utf-8")
        if self._port == 8002:
            token_query = f"&token={self._token}" if self._token else ""
            url = (
                f"wss://{self._host}:{self._port}/api/v2/channels/"
                f"samsung.remote.control?name={encoded_name}{token_query}"
            )
            sslopt: dict[str, Any] = {"cert_reqs": ssl.CERT_NONE}
        else:
            url = (
                f"ws://{self._host}:{self._port}/api/v2/channels/"
                f"samsung.remote.control?name={encoded_name}"
            )
            sslopt = {}

        try:
            connection = websocket.create_connection(
                url,
                timeout=max(self._timeout, DEFAULT_WS_TIMEOUT),
                sslopt=sslopt,
            )
            response = connection.recv()
            self._store_token(response)
        except (OSError, socket.error, websocket.WebSocketException) as err:
            if allow_token_reset and self._token and self._port == 8002:
                self._token = None
                self._save_token()
                return self._create_ws_connection_inner(allow_token_reset=False)
            raise TizenRemasteredConnectionError(str(err)) from err

        return connection

    def _store_token(self, response: str) -> None:
        """Store the Samsung token if the TV provides one."""
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            return

        token = payload.get("data", {}).get("token")
        if token:
            self._token = str(token)
            self._save_token()

    def _load_token(self) -> str | None:
        """Load a cached Samsung token from disk."""
        if not self._token_path or not self._token_path.exists():
            return None

        try:
            token = self._token_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None

        return token or None

    def _save_token(self) -> None:
        """Persist the Samsung token to disk."""
        if not self._token_path:
            return

        try:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(self._token or "", encoding="utf-8")
        except OSError:
            return
