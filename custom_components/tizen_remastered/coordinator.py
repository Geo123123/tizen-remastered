"""Data coordinator for Tizen Remastered."""

from __future__ import annotations

from datetime import timedelta
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import SamsungTizenClient, TVStatus, TizenRemasteredConnectionError
from .const import CONF_MAC, CONF_PORT, CONF_WS_NAME, DEFAULT_NAME, DEFAULT_PORT, DEFAULT_TIMEOUT, DEFAULT_WS_NAME, DOMAIN


class TizenRemasteredCoordinator(DataUpdateCoordinator[TVStatus]):
    """Coordinate updates for a Samsung Tizen TV."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        safe_host = re.sub(r"[^a-zA-Z0-9_.-]", "_", entry.data[CONF_HOST])
        self.client = SamsungTizenClient(
            host=entry.data[CONF_HOST],
            port=entry.data.get(CONF_PORT, DEFAULT_PORT),
            timeout=entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ws_name=entry.data.get(CONF_WS_NAME, DEFAULT_WS_NAME),
            mac=entry.data.get(CONF_MAC),
            token_path=hass.config.path(".storage", f"tizen_remastered_token_{safe_host}.txt"),
        )

        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"{DOMAIN}_{entry.data.get(CONF_NAME, DEFAULT_NAME)}",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self) -> TVStatus:
        """Fetch data from the TV."""
        try:
            return await self.hass.async_add_executor_job(self.client.get_status)
        except TizenRemasteredConnectionError as err:
            raise UpdateFailed(str(err)) from err
