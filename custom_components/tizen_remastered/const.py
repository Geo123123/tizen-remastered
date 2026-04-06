"""Constants for the Tizen Remastered integration."""

DOMAIN = "tizen_remastered"

CONF_APP_LIST = "app_list"
CONF_MAC = "mac"
CONF_PORT = "port"
CONF_WS_NAME = "ws_name"

DEFAULT_NAME = "Samsung TV Remastered"
DEFAULT_PORT = 8002
DEFAULT_TIMEOUT = 3.0
DEFAULT_WS_NAME = "Home Assistant"

DATA_COORDINATOR = "coordinator"
MANUFACTURER = "Samsung"

DEFAULT_SOURCE_LIST: dict[str, str] = {
    "TV": "KEY_TV",
    "HDMI 1": "KEY_HDMI1",
    "HDMI 2": "KEY_HDMI2",
    "HDMI 3": "KEY_HDMI3",
    "HDMI 4": "KEY_HDMI4",
}
