"""Common entity behavior and automatically populated device page."""
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN, NAME, VERSION


class MonitorEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, monitor, suffix):
        self.monitor = monitor
        self._attr_unique_id = f"{monitor.entry.entry_id}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, monitor.entry.entry_id)}, name=NAME,
            manufacturer="WattWatch", model="Local power pattern monitor", sw_version=VERSION)

    async def async_added_to_hass(self):
        self.async_on_remove(async_dispatcher_connect(
            self.hass, self.monitor.signal, self._updated))

    @callback
    def _updated(self):
        self.async_write_ha_state()
