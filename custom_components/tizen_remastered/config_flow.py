"""Config flow for Tizen Remastered."""

from __future__ import annotations

import json

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TIMEOUT
from homeassistant.data_entry_flow import FlowResult

from .client import SamsungTizenClient
from .const import (
    CONF_APP_LIST,
    CONF_MAC,
    CONF_PORT,
    CONF_WS_NAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_WS_NAME,
    DOMAIN,
    parse_app_list,
)


class TizenRemasteredConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tizen Remastered."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                parse_app_list(user_input.get(CONF_APP_LIST))
            except (ValueError, json.JSONDecodeError):
                errors["base"] = "invalid_app_list"
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                if await self._async_can_connect(user_input):
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, DEFAULT_NAME),
                        data=user_input,
                    )

                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
                vol.Optional(CONF_WS_NAME, default=DEFAULT_WS_NAME): str,
                vol.Optional(CONF_MAC): str,
                vol.Optional(CONF_APP_LIST): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured(updates=user_input)

        return self.async_create_entry(
            title=user_input.get(CONF_NAME, DEFAULT_NAME),
            data=user_input,
        )

    async def _async_can_connect(self, user_input: dict) -> bool:
        """Validate the user input allows us to connect."""
        client = SamsungTizenClient(
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            timeout=user_input[CONF_TIMEOUT],
            ws_name=user_input[CONF_WS_NAME],
            mac=user_input.get(CONF_MAC),
        )
        status = await self.hass.async_add_executor_job(client.get_status)
        return status.is_on
