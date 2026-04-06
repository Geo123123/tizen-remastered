"""Media player platform for Tizen Remastered."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DEFAULT_NAME, DOMAIN, MANUFACTURER
from .coordinator import TizenRemasteredCoordinator

MEDIA_TYPE_KEY = "send_key"
MEDIA_TYPE_BROWSER = "browser"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player entity."""
    coordinator: TizenRemasteredCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([TizenRemasteredMediaPlayer(coordinator, entry)])


class TizenRemasteredMediaPlayer(
    CoordinatorEntity[TizenRemasteredCoordinator], MediaPlayerEntity
):
    """Representation of a Samsung Tizen TV."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_has_entity_name = True
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.PLAY_MEDIA
    )

    def __init__(self, coordinator: TizenRemasteredCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    @property
    def state(self) -> str:
        """Return the entity state."""
        return STATE_ON if self.coordinator.data.is_on else STATE_OFF

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "manufacturer": MANUFACTURER,
            "model": self.coordinator.data.model,
            "name": self.coordinator.data.friendly_name or self._attr_name,
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}:8001/api/v2/",
        }

    @property
    def media_title(self) -> str | None:
        """Return a simple media title."""
        return self.coordinator.data.device_name

    async def async_turn_on(self) -> None:
        """Turn the TV on."""
        await self.hass.async_add_executor_job(self.coordinator.client.turn_on)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self.hass.async_add_executor_job(self.coordinator.client.send_key, "KEY_POWER")
        await self.coordinator.async_request_refresh()

    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        **kwargs,
    ) -> None:
        """Play media or send a command."""
        if media_type == MEDIA_TYPE_KEY:
            await self.hass.async_add_executor_job(self.coordinator.client.send_key, media_id)
        elif media_type == MediaType.APP:
            await self.hass.async_add_executor_job(self.coordinator.client.launch_app, media_id)
        elif media_type == MEDIA_TYPE_BROWSER:
            await self.hass.async_add_executor_job(self.coordinator.client.open_browser, media_id)
        elif media_type == MediaType.URL:
            await self.hass.async_add_executor_job(self.coordinator.client.open_browser, media_id)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")

        await self.coordinator.async_request_refresh()
