"""Exercise the real Home Assistant loader, config flow, entities and storage.

Run in the declared minimum-version environment (Home Assistant 2024.12.5).
These tests do not connect to a household or external device.
"""
import shutil
from pathlib import Path
from datetime import timedelta
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from homeassistant import loader
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr, area_registry as ar
from homeassistant.util import dt as dt_util


@pytest.mark.asyncio
async def test_install_discover_options_reload_storage_and_unload(tmp_path):
    source = Path(__file__).parents[1] / "custom_components/wattwatch"
    shutil.copytree(source, tmp_path / "custom_components/wattwatch")
    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    hass.config_entries = ConfigEntries(hass, {})
    await hass.config_entries.async_initialize()
    await ar.async_load(hass)
    await dr.async_load(hass)
    await er.async_load(hass)
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    try:
        assert await async_setup_component(hass, "persistent_notification", {})
        hass.states.async_set("sensor.fridge_power", "100", {
            "unit_of_measurement": "W", "device_class": "power", "friendly_name": "Koelkast"})
        hass.states.async_set("sensor.p1_meter_vermogen", "500", {
            "unit_of_measurement": "W", "device_class": "power"})
        result = await hass.config_entries.flow.async_init("wattwatch", context={"source": "user"})
        assert result["type"] == "form" and not result["data_schema"].schema
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == "create_entry"
        await hass.async_block_till_done()
        entry = result["result"]
        assert entry.state is ConfigEntryState.LOADED
        monitor = entry.runtime_data
        assert len(monitor.selected) == 1
        assert "sensor.p1_meter_vermogen" in monitor.rejected
        registry = er.async_get(hass)
        entity_ids = [r.entity_id for r in er.async_entries_for_config_entry(registry, entry.entry_id)]
        assert len(entity_ids) == 3  # Overview, overall alarm, appliance status.
        assert any(hass.states.get(eid).state == "learning" for eid in entity_ids)
        # New power entities are picked up on the next minute without setup.
        hass.states.async_set("sensor.new_kettle_power", "0.2", {
            "unit_of_measurement": "kW", "device_class": "power"})
        monitor.tick(dt_util.utcnow() + timedelta(minutes=1))
        await hass.async_block_till_done()
        assert len(monitor.selected) == 2
        assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 4
        assert monitor.profiles["sensor.new_kettle_power"].current_watts == 200
        duplicate = await hass.config_entries.flow.async_init("wattwatch", context={"source": "user"})
        assert duplicate["type"] == "abort"
        options = await hass.config_entries.options.async_init(entry.entry_id)
        assert options["type"] == "form"
        options = await hass.config_entries.options.async_configure(options["flow_id"], {
            "notifications": False, "excluded": ["sensor.new_kettle_power"], "included": []})
        assert options["type"] == "create_entry"
        await hass.async_block_till_done()
        monitor = entry.runtime_data
        assert len(monitor.selected) == 1
        assert monitor.options["notifications"] is False
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert monitor.closed
        assert (tmp_path / ".storage" / f"wattwatch.{entry.entry_id}").is_file()
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(entry.runtime_data.selected) == 1
        assert await hass.config_entries.async_remove(entry.entry_id)
        assert not (tmp_path / ".storage" / f"wattwatch.{entry.entry_id}").exists()
    finally:
        await hass.async_stop(force=True)
