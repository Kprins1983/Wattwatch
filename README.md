# WattWatch

**Automatically learns each device’s normal power use in Home Assistant and alerts you to sustained changes.**

WattWatch discovers existing power sensors, builds a separate local baseline for each one, and flags sustained unusual hourly averages. Ordinary setup needs one confirmation. No YAML, helpers, cloud account, MQTT or Node-RED are needed. Existing appliance power sensors are required.

## Install with HACS

1. In HACS, open **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/Kprins1983/Wattwatch` and choose **Integration**.
3. Install WattWatch and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → WattWatch** and submit the start form.
5. Open the WattWatch device page to see the automatic overview and appliance statuses.

## Install manually

Copy `custom_components/wattwatch` to the `custom_components` directory of your Home Assistant configuration, restart Home Assistant, then add WattWatch under **Settings → Devices & services**. See [LEESMIJ_EERST.md](LEESMIJ_EERST.md) for the Dutch step-by-step guide.

## What to expect

WattWatch scans power sensors once a minute and begins learning automatically. It needs at least seven days of observations and enough valid readings before it assesses a pattern. Alerts appear as Home Assistant notifications after two consecutive valid hours sit outside the device’s usual range. The overview and status sensors appear on the built-in WattWatch device page; no dashboard card needs to be installed.

Sensor selection uses common naming clues to skip likely whole-home meters, batteries and generation sensors. Check the discovered list after setup. Optional integration settings let you exclude or explicitly include sensors and turn off notifications. Role detection cannot be perfect because Home Assistant has no universal field that identifies a sensor as an appliance meter or a whole-home meter.

All learning data stays in Home Assistant. WattWatch makes no cloud requests. An alert indicates a sustained change in measured power; it does not diagnose a device fault. See [LEESMIJ_EERST.md](LEESMIJ_EERST.md) for limitations and details of the learning period.

## Development

The isolated integration lifecycle and detector tests were run with Python 3.12.14 and Home Assistant 2024.12.5. This prototype still needs testing on current Home Assistant releases and with household devices before it can be called stable.

```sh
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Report bugs or suggestions in [GitHub Issues](https://github.com/Kprins1983/Wattwatch/issues).
