"""Config flow for Extended Conversation Client."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_SERVER_URL,
    DEFAULT_SERVER_URL,
    CONF_SERVER_ENABLED,
    DEFAULT_SERVER_ENABLED,
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Extended Conversation Client",
                data={
                    CONF_SERVER_URL: user_input.get(CONF_SERVER_URL, DEFAULT_SERVER_URL),
                    CONF_SERVER_ENABLED: user_input.get(CONF_SERVER_ENABLED, DEFAULT_SERVER_ENABLED),
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SERVER_URL,
                        default=DEFAULT_SERVER_URL
                    ): str,
                    vol.Optional(
                        CONF_SERVER_ENABLED,
                        default=DEFAULT_SERVER_ENABLED
                    ): bool,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SERVER_URL,
                        default=self.config_entry.options.get(
                            CONF_SERVER_URL, DEFAULT_SERVER_URL
                        ),
                    ): str,
                    vol.Optional(
                        CONF_SERVER_ENABLED,
                        default=self.config_entry.options.get(
                            CONF_SERVER_ENABLED, DEFAULT_SERVER_ENABLED
                        ),
                    ): bool,
                }
            ),
        )