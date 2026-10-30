"""WattWatch: zero-configuration local power pattern monitoring."""
from .const import PLATFORMS
from .coordinator import Monitor


async def async_setup_entry(hass, entry):
    monitor = Monitor(hass, entry)
    await monitor.async_load()
    entry.runtime_data = monitor
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    monitor.start()
    return True


async def _async_options_updated(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_close()
        return True
    return False


async def async_remove_entry(hass, entry):
    from homeassistant.helpers.storage import Store
    from .const import DOMAIN
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()
