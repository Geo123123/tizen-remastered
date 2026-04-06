"""Constants for the Tizen Remastered integration."""

from __future__ import annotations

import json
from typing import Any

DOMAIN = "tizen_remastered"

CONF_API_KEY = "api_key"
CONF_APP_LIST = "app_list"
CONF_DEVICE_ID = "device_id"
CONF_MAC = "mac"
CONF_PORT = "port"
CONF_WS_NAME = "ws_name"

DEFAULT_NAME = "Samsung TV Remastered"
DEFAULT_PORT = 8002
DEFAULT_TIMEOUT = 3.0
DEFAULT_WS_NAME = "Home Assistant"
DEFAULT_WS_TIMEOUT = 10.0

DATA_COORDINATOR = "coordinator"
MANUFACTURER = "Samsung"

DEFAULT_SOURCE_LIST: dict[str, str] = {
    "TV": "KEY_TV",
    "HDMI 1": "KEY_HDMI",
    "HDMI 2": "KEY_HDMI",
    "HDMI 3": "KEY_HDMI",
    "HDMI 4": "KEY_HDMI",
}


def parse_app_list(value: str | dict[str, str] | None) -> dict[str, str]:
    """Parse an app list from config input."""
    if value is None:
        return {}

    if isinstance(value, dict):
        return {str(key): str(app_id) for key, app_id in value.items()}

    value = value.strip()
    if not value:
        return {}

    parsed: Any = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("App list must be a JSON object")

    return {str(key): str(app_id) for key, app_id in parsed.items()}
