"""Automatic overview and one status entity per discovered power channel."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from .entity import MonitorEntity

STATES = ["learning", "normal", "anomaly", "unavailable", "excluded", "insufficient_data"]


async def async_setup_entry(hass, entry, async_add_entities):
    monitor = entry.runtime_data
    async_add_entities([Overview(monitor)])
    seen = set()

    @callback
    def discover(keys):
        new = set(keys) - seen
        seen.update(new)
        async_add_entities([Appliance(monitor, key) for key in sorted(new)])

    monitor.listeners.append(discover)
    entry.async_on_unload(lambda: monitor.listeners.remove(discover))


class Overview(MonitorEntity, SensorEntity):
    _attr_translation_key = "overview"
    _attr_icon = "mdi:flash-eye"

    def __init__(self, monitor):
        super().__init__(monitor, "overview")

    @property
    def native_value(self):
        return len(self.monitor.selected)

    @property
    def extra_state_attributes(self):
        counts = {state: 0 for state in STATES}
        for key in self.monitor.selected:
            counts[self.monitor.state(key)] += 1
        return {**counts, "excluded_sensors": self.monitor.rejected,
                "learning_days": 7, "notification_location": "Home Assistant",
                "sample_interval_seconds": 60}


class Appliance(MonitorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATES
    _attr_translation_key = "appliance"
    _attr_icon = "mdi:chart-bell-curve-cumulative"

    def __init__(self, monitor, key):
        super().__init__(monitor, key)
        self.key = key

    @property
    def name(self):
        eid = self.monitor.sources.get(self.key)
        state = self.monitor.hass.states.get(eid) if eid else None
        return state.name if state else eid or self.key

    @property
    def native_value(self):
        return self.monitor.state(self.key)

    @property
    def extra_state_attributes(self):
        profile = self.monitor.profiles[self.key]
        return {"source_entity": self.monitor.sources.get(self.key),
                "learning_percent": profile.progress(dt_util.utcnow().timestamp()),
                "learned_hours": len(profile.history),
                **profile.last_evaluation}
