"""One overall anomaly entity for the default device overview."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .entity import MonitorEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([Anomaly(entry.runtime_data)])


class Anomaly(MonitorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "anomaly"

    def __init__(self, monitor):
        super().__init__(monitor, "anomaly")

    @property
    def is_on(self):
        return any(self.monitor.state(key) == "anomaly" for key in self.monitor.selected)

    @property
    def extra_state_attributes(self):
        return {"devices": [self.monitor.sources[key] for key in sorted(self.monitor.selected)
                            if self.monitor.state(key) == "anomaly"]}
