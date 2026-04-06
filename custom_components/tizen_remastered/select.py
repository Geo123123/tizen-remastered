"""Select entities for Tizen Remastered."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_APP_LIST,
    DATA_COORDINATOR,
    DEFAULT_SOURCE_LIST,
    DOMAIN,
    MANUFACTURER,
    parse_app_list,
)
from .coordinator import TizenRemasteredCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator: TizenRemasteredCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[SelectEntity] = [TizenSourceSelect(coordinator, entry)]

    app_list = parse_app_list(entry.data.get(CONF_APP_LIST))
    if app_list:
        entities.append(TizenAppSelect(coordinator, entry, app_list))

    async_add_entities(entities)


class TizenBaseSelect(CoordinatorEntity[TizenRemasteredCoordinator], SelectEntity):
    """Base select entity tied to the same device."""

    def __init__(self, coordinator: TizenRemasteredCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=self.coordinator.data.model,
            name=self.coordinator.data.friendly_name or self._entry.title,
        )


class TizenSourceSelect(TizenBaseSelect):
    """Select TV inputs."""

    _attr_has_entity_name = True
    _attr_name = "Source"

    def __init__(self, coordinator: TizenRemasteredCoordinator, entry: ConfigEntry) -> None:
        """Initialize the source selector."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_source_select"
        self._attr_options = list(DEFAULT_SOURCE_LIST)
        self._attr_current_option = self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Change the TV source."""
        await self.hass.async_add_executor_job(
            self.coordinator.client.send_key,
            DEFAULT_SOURCE_LIST[option],
        )
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class TizenAppSelect(TizenBaseSelect):
    """Select and launch configured TV apps."""

    _attr_has_entity_name = True
    _attr_name = "App"

    def __init__(
        self,
        coordinator: TizenRemasteredCoordinator,
        entry: ConfigEntry,
        app_list: dict[str, str],
    ) -> None:
        """Initialize the app selector."""
        super().__init__(coordinator, entry)
        self._app_list = app_list
        self._attr_unique_id = f"{entry.entry_id}_app_select"
        self._attr_options = list(app_list)
        self._attr_current_option = self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Launch the selected TV app."""
        await self.hass.async_add_executor_job(
            self.coordinator.client.launch_app,
            self._app_list[option],
        )
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
