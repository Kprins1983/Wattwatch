"""Discover devices and sample them locally once a minute."""
from datetime import timedelta
import logging

from homeassistant.components import persistent_notification
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULTS
from .discovery import select
from .engine import Profile, watts, DAY, RETENTION

_LOGGER = logging.getLogger(__name__)


class Monitor:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.options = DEFAULTS | dict(entry.options)
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.profiles = {}
        self.sources = {}
        self.selected = set()
        self.rejected = {}
        self.listeners = []
        self.signal = f"{DOMAIN}_{entry.entry_id}"
        self._unsub = None
        self.closed = False

    async def async_load(self):
        stored = await self.store.async_load() or {}
        for key, value in stored.get("profiles", {}).items():
            self.profiles[key] = Profile.load(value)

    def serialize(self):
        return {"profiles": {k: p.dump() for k, p in self.profiles.items()}}

    @callback
    def start(self):
        self.tick(dt_util.utcnow())
        self._unsub = async_track_time_interval(self.hass, self.tick, timedelta(minutes=1))

    @callback
    def tick(self, now):
        if self.closed:
            return
        registry = er.async_get(self.hass)
        candidates = []
        for state in self.hass.states.async_all("sensor"):
            entity = registry.async_get(state.entity_id)
            candidates.append({"id": state.entity_id,
                               "name": state.name,
                               "unit": state.attributes.get("unit_of_measurement"),
                               "device_class": state.attributes.get("device_class"),
                               "device_id": entity.device_id if entity else None,
                               "platform": entity.platform if entity else None,
                               "disabled": bool(entity and entity.disabled_by)})
        ids, self.rejected = select(candidates, self.options["included"], self.options["excluded"])
        selected = set()
        added = []
        for eid in ids:
            entity = registry.async_get(eid)
            # Registry IDs survive an entity rename. Unregistered template
            # sensors fall back to the entity ID until a unique_id is supplied.
            key = entity.id if entity else eid
            selected.add(key)
            self.sources[key] = eid
            if key not in self.profiles:
                self.profiles[key] = Profile()
            added.append(key)
        self.selected = selected
        ts = now.timestamp()
        local = dt_util.as_local(now)
        for key in selected:
            profile = self.profiles[key]
            state = self.hass.states.get(self.sources[key])
            value = watts(state.state, state.attributes.get("unit_of_measurement")) if state else None
            result = profile.sample(ts, value, local.hour, local.date().isoformat())
            if result and result["status"] == "anomaly":
                if self.options["notifications"] and ts - profile.last_alert >= DAY:
                    self.notify(key, result)
                    profile.last_alert = ts
            elif result and result["status"] == "normal":
                persistent_notification.async_dismiss(self.hass, f"{DOMAIN}_{key}")
        for key in self.profiles.keys() - selected:
            profile = self.profiles[key]
            profile.history = [r for r in profile.history if r["start"] >= ts - RETENTION]
            profile.reset_continuity()
            profile.previous_time = profile.previous_watts = None
            profile.bucket = None
            profile.integral = profile.coverage = 0
            profile.available = False
        # Platform listeners keep their own seen set; callbacks are idempotent.
        for listener in self.listeners:
            listener(added)
        async_dispatcher_send(self.hass, self.signal)
        self.store.async_delay_save(self.serialize, 300)

    @callback
    def notify(self, key, result):
        eid = self.sources[key]
        state = self.hass.states.get(eid)
        name = state.name if state else eid
        nl = self.hass.config.language == "nl"
        high = result["direction"] == "high"
        if nl:
            direction = "hoger" if high else "lager"
            title = f"WattWatch: afwijkend verbruik — {name}"
            message = (f"**{name}** heeft twee opeenvolgende volledige meeturen {direction} "
                       f"verbruik dan de gebruikelijke bandbreedte op vergelijkbare uren.\n\n"
                       f"Laatste uurgemiddelde: **{result['average_watts']:.0f} W**. "
                       f"Referentiemediaan: **{result['expected_watts']:.0f} W**.\n\n"
                       "Dit is een verandering in gemeten verbruik, geen vastgestelde storing.")
        else:
            direction = "higher" if high else "lower"
            title = f"WattWatch: unusual consumption — {name}"
            message = (f"**{name}** used {direction} power than its usual range for two "
                       f"consecutive measured hours at comparable times.\n\n"
                       f"Latest hourly average: **{result['average_watts']:.0f} W**. "
                       f"Reference median: **{result['expected_watts']:.0f} W**.\n\n"
                       "This indicates a consumption change, not a diagnosed fault.")
        persistent_notification.async_create(self.hass, message, title, f"{DOMAIN}_{key}")
        self.hass.bus.async_fire(f"{DOMAIN}_anomaly", {"entity_id": eid, **result})

    def state(self, key):
        if key not in self.selected:
            return "excluded" if self.sources.get(key) in self.rejected else "unavailable"
        return self.profiles[key].status(dt_util.utcnow().timestamp())

    async def async_close(self):
        self.closed = True
        if self._unsub:
            self._unsub()
        await self.store.async_save(self.serialize())
