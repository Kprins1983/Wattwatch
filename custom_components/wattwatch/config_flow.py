"""One confirmation to start. All technical choices are optional."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULTS, NAME


class WattWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WattWatchOptionsFlow()


class WattWatchOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        options = DEFAULTS | dict(self.config_entry.options)
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        sensor_selector = selector.EntitySelector(selector.EntitySelectorConfig(
            domain="sensor", multiple=True))
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional("notifications", default=options["notifications"]): bool,
            vol.Optional("excluded", default=options["excluded"]): sensor_selector,
            vol.Optional("included", default=options["included"]): sensor_selector,
        }))
