"""Media player platform for Tizen Remastered."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DEFAULT_NAME,
    DEFAULT_SOURCE_LIST,
    DOMAIN,
    MANUFACTURER,
)
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
    _attr_has_entity_name = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, coordinator: TizenRemasteredCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.title or entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_is_volume_muted = False
        self._attr_source = None
        self._attr_source_list = list(DEFAULT_SOURCE_LIST)

    @property
    def state(self) -> MediaPlayerState:
        """Return the entity state."""
        return MediaPlayerState.ON if self.coordinator.data.is_on else MediaPlayerState.OFF

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

    async def _async_send_key(self, key: str) -> None:
        """Send a remote key and refresh state."""
        await self.hass.async_add_executor_job(self.coordinator.client.send_key, key)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the TV on."""
        await self.hass.async_add_executor_job(self.coordinator.client.turn_on)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self._async_send_key("KEY_POWER")

    async def async_volume_up(self) -> None:
        """Turn volume up."""
        await self._async_send_key("KEY_VOLUP")

    async def async_volume_down(self) -> None:
        """Turn volume down."""
        await self._async_send_key("KEY_VOLDOWN")

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the TV."""
        await self._async_send_key("KEY_MUTE")
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        """Send play."""
        await self._async_send_key("KEY_PLAY")

    async def async_media_pause(self) -> None:
        """Send pause."""
        await self._async_send_key("KEY_PAUSE")

    async def async_media_stop(self) -> None:
        """Send stop."""
        await self._async_send_key("KEY_STOP")

    async def async_media_next_track(self) -> None:
        """Go to next item or channel."""
        await self._async_send_key("KEY_CHUP")

    async def async_media_previous_track(self) -> None:
        """Go to previous item or channel."""
        await self._async_send_key("KEY_CHDOWN")

    async def async_select_source(self, source: str) -> None:
        """Select a TV source."""
        key = DEFAULT_SOURCE_LIST.get(source)
        if key is None:
            raise ValueError(f"Unsupported source: {source}")

        await self._async_send_key(key)
        self._attr_source = source
        self.async_write_ha_state()

    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        **kwargs,
    ) -> None:
        """Play media or send a command."""
        if media_type == MEDIA_TYPE_KEY:
            await self._async_send_key(media_id)
            return
        elif media_type == MediaType.APP:
            await self.hass.async_add_executor_job(self.coordinator.client.launch_app, media_id)
        elif media_type == MEDIA_TYPE_BROWSER:
            await self.hass.async_add_executor_job(self.coordinator.client.open_browser, media_id)
        elif media_type == MediaType.URL:
            await self.hass.async_add_executor_job(self.coordinator.client.open_browser, media_id)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")

        await self.coordinator.async_request_refresh()
