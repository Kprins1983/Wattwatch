# WattWatch

<p align="center"><img src="assets/wattwatch-logo.svg" alt="WattWatch" width="750"></p>

**Local power monitoring for Home Assistant: learn normal appliance usage and notice sustained changes.**

English documentation below · [Nederlandse uitleg](#nederlandse-uitleg)

WattWatch discovers existing appliance power sensors, learns their usual hourly consumption patterns and notifies you when measured power stays unusually high or low. Setup takes one confirmation; no helpers, YAML, MQTT, Node-RED, subscription or cloud account are needed for the monitoring itself.

**Version 0.1.0 is a test release.** It needs real household testing and testing on current Home Assistant versions. A change in power consumption is a signal to investigate, not a diagnosis of a faulty appliance.

## What WattWatch does

- Discovers power sensors every minute and converts W, kW and mW to watts.
- Builds a separate local history for each selected power channel.
- Calculates time-weighted hourly averages instead of reacting to every short peak.
- Compares completed hours with earlier days around the same local time.
- Confirms an anomaly after two consecutive valid hours outside the normal band in the same direction.
- Creates an overview sensor, an overall problem sensor and individual appliance status sensors.
- Shows these entities on the built-in WattWatch device page.
- Posts persistent notifications inside Home Assistant.
- Saves learning data locally and restores completed-hour history after a restart.

For example, a refrigerator that runs at unusually high power for several hours may trigger a notification after learning. A short kettle cycle is not the kind of change WattWatch is designed to detect. These are illustrative scenarios, not guaranteed detection outcomes.

## Requirements and languages

You need Home Assistant and existing **power sensors for individual appliances**. A smart plug with power measurement is one possible source. A plain on/off switch or an energy-only sensor in kWh is not enough.

The declared minimum Home Assistant version is 2024.12.0. The documented isolated tests used 2024.12.5; newer versions still require practical verification. **The bundled integration icon requires Home Assistant 2026.3 or newer.**

The interface includes **English and Dutch**. Users can install the public repository internationally; there is no country setting or country-specific electricity tariff requirement. Compatibility depends on the available power sensors and Home Assistant setup. More interface languages can be contributed through GitHub.

## Install through HACS

If WattWatch is not in your catalog, add it as a custom repository:

1. Open HACS and its **Custom repositories** menu.
2. Enter `https://github.com/Kprins1983/Wattwatch`.
3. Choose **Integration** as the category and add the repository.
4. Find WattWatch, download it and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **WattWatch**, open it and submit the start form.
7. Open the WattWatch integration and its device page to check the discovered sensors.

HACS menu names can vary by version. Downloading the files and adding the integration are separate steps.

## Manual installation

1. Download and extract the repository.
2. Copy the complete `custom_components/wattwatch` directory into your Home Assistant configuration directory's `custom_components` folder.
3. Keep all subfolders, including `brand` and `translations`.
4. Restart Home Assistant and add WattWatch through **Settings → Devices & services**.

The result should include:

```text
/config/custom_components/wattwatch/
├── __init__.py
├── manifest.json
├── brand/
│   └── icon.png
└── translations/
    ├── en.json
    └── nl.json
```

This is a partial directory listing; copy the complete integration, not just these files.

## Icon after installation

WattWatch includes its existing icon at `custom_components/wattwatch/brand/icon.png`. Home Assistant 2026.3+ supports this local branding automatically; users do not need to upload an icon themselves. See the [Home Assistant branding documentation](https://contributors.home-assistant.io/core/integrations/brands/).

After installing or updating, restart Home Assistant and refresh the browser or app. If necessary, download the integration again and check that the `brand` folder is present.

The icon shown in the **HACS catalog** depends on HACS's support for local brand images. Some versions have a [reported local-icon display issue](https://github.com/hacs/integration/issues/5171). A missing HACS catalog image alone does not mean installation failed. The integration logo, entity icons and GitHub account avatar are separate images.

## Learning and alerts

The first assessment needs all of the following:

- At least **7 days** since the first observation.
- At least **120 usable hours** in retained history.
- Reference measurements around the same local hour on at least **5 earlier days**.

An hour needs at least **45 minutes of valid coverage**. Unknown, unavailable, negative and non-finite readings do not count as zero. Long gaps interrupt continuity. Existing Home Assistant Recorder history is not imported, so learning starts when WattWatch starts collecting data.

The comparison uses earlier days at the same local hour and the hour before/after. Its statistical band allows for normal variation. Two consecutive valid hours must fall outside that band in the same direction; a notification therefore generally takes about **2–3 hours of sustained change**, once enough reference data exists.

Notifications appear inside Home Assistant. There is a 24-hour notification cooldown per channel. The same persistent notification is updated instead of stacked and is dismissed after a normally evaluated hour. Restarting preserves reference history but resets the two-hour confirmation.

**Phone push notifications are not built in.** The integration does not currently account for outdoor temperature, weekdays versus weekends or appliance program selection.

## Automatic overview

No custom dashboard card is required. Open **Settings → Devices & services → WattWatch → WattWatch device**.

| Entity | Meaning |
| --- | --- |
| Overview / Gevolgde apparaten | Number of selected power channels, plus status counts in its attributes |
| Anomaly / Afwijkend verbruik | Overall problem sensor: on when any selected channel has a confirmed anomaly |
| Individual appliance sensor | Learning, normal, anomaly, unavailable or insufficient-data status |

Separate power channels of one physical appliance can appear separately. The overview counts channels, which is not always the number of physical appliances.

Individual status sensor attributes include `source_entity`, `learning_percent` and `learned_hours`. After a usable evaluation, additional attributes can include `average_watts`, `expected_watts`, `lower_watts`, `upper_watts` and `direction`. These evaluation values describe a completed hour, not live power.

## Dashboard card examples

<p align="center"><img src="assets/wattwatch-dashboard-example.png" alt="WattWatch dashboard concept showing monitored channels and learning status" width="350"></p>

*Dashboard concept — this custom card is not installed automatically. The examples below use standard Home Assistant cards and have a different appearance.*

These examples use **built-in Home Assistant cards**. No additional frontend plugin is required. They are optional; WattWatch does not install them automatically.

**Replace every example entity ID with your own.** Entity IDs depend on the installation language, source sensor names and any renaming. Find them under **Developer tools → States** or on the WattWatch device page. For an appliance status entity, its `source_entity` attribute identifies the original power sensor.

On a dashboard, choose **Edit dashboard → Add card → Manual** and paste one example. Menu labels may vary.

### 1. Compact overview

Shows the number of monitored channels and whether a confirmed anomaly exists.

```yaml
type: entities
title: WattWatch
show_header_toggle: false
entities:
  - entity: sensor.wattwatch_gevolgde_apparaten
    name: Monitored channels
  - entity: binary_sensor.wattwatch_afwijkend_verbruik
    name: Unusual power use
```

### 2. Appliance status and learning progress

Use the individual WattWatch status entity, not the original power sensor, for this card. The example ID is a placeholder.

```yaml
type: entities
title: Refrigerator monitoring
show_header_toggle: false
entities:
  - entity: sensor.wattwatch_refrigerator
    name: Status
  - type: attribute
    entity: sensor.wattwatch_refrigerator
    attribute: learning_percent
    name: Learning progress
    suffix: "%"
  - type: attribute
    entity: sensor.wattwatch_refrigerator
    attribute: learned_hours
    name: Retained learning hours
```

Progress reaching 100% does not by itself guarantee sufficient same-hour references for every assessment.

### 3. Power history

Use the **original appliance power sensors** for a power graph. WattWatch's individual sensors contain text statuses, not a live watt reading.

```yaml
type: history-graph
title: Appliance power — last 24 hours
hours_to_show: 24
entities:
  - entity: sensor.refrigerator_power
    name: Refrigerator
  - entity: sensor.freezer_power
    name: Freezer
```

Home Assistant Recorder must retain those sensors for the history graph to have data. This chart uses Recorder history; the WattWatch detector uses its own locally collected hourly history.

### 4. Warning shown only during an anomaly

Replace the binary sensor ID in the condition.

```yaml
type: conditional
conditions:
  - entity: binary_sensor.wattwatch_afwijkend_verbruik
    state: "on"
card:
  type: markdown
  title: WattWatch warning
  content: |
    Unusual power consumption has been detected.
    Open the WattWatch device page to see which appliance is affected.
    Check the appliance and its measurements before drawing conclusions.
```

## Sensor selection and settings

WattWatch uses naming clues to skip likely whole-home meters, solar generation, batteries and totals. Automatic selection is imperfect: Home Assistant does not provide a universal appliance-versus-total classification.

Under the integration's **Configure** options you can:

- Disable Home Assistant notifications.
- Exclude sensors.
- Explicitly include suitable power sensors that were automatically skipped.

Exclusion takes priority. Including a kWh sensor does not turn it into a power sensor. Clear same-name aliases on the same registered device can be deduplicated; unrelated duplicates may still need manual exclusion.

## Privacy, storage and removal

WattWatch itself makes no cloud requests. Your existing smart plug or meter integrations may have their own network behavior.

Up to 21 days of usable hourly averages are retained locally. Data is saved approximately every five minutes and on a normal reload. A power failure may lose the most recent unsaved data. The unfinished current hour is rebuilt after restarting.

Removing the integration through Home Assistant removes WattWatch's stored learning data. Recorder history follows Home Assistant's normal retention settings. To deliberately learn a completely new baseline, remove and re-add the integration.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| No appliances found | Source entities must report power in W, kW or mW; review automatic exclusions and Configure options |
| Still learning after a week | Check usable-hour count, sensor gaps and sufficient earlier-day references |
| Missing integration icon | Use Home Assistant 2026.3+, keep the brand folder, restart and refresh |
| Missing HACS catalog icon | Check your HACS version and its local-brand support |
| Dashboard says entity not found | Replace example entity IDs with the actual IDs from your installation |
| No power chart | Use original numeric power sensors and check Recorder history |
| No phone notification | This release provides persistent Home Assistant notifications, not phone push |

## International availability and contributions

The public repository can be installed through HACS as a custom repository or manually. This is separate from acceptance into the default HACS catalog.

Default catalog inclusion requires the publisher's submission and review. HACS documents successful HACS/Hassfest checks and a GitHub release among its submission requirements. See the [official publishing guide](https://github.com/hacs/documentation/blob/main/source/docs/publish/include.md).

Please report bugs in [GitHub Issues](https://github.com/Kprins1983/Wattwatch/issues), preferably in English so others can join the discussion. Include Home Assistant and HACS versions, WattWatch version, reproduction steps and relevant logs with private details removed.

Translation contributions are welcome in `custom_components/wattwatch/translations/`. Keep translation keys consistent with `strings.json`; do not translate internal state values or entity attribute keys.

## Development and test status

The documented isolated tests passed with Python 3.12.14 and Home Assistant 2024.12.5. See [TESTRESULTATEN.md](TESTRESULTATEN.md) for their scope. These historical results do not establish compatibility with every newer Home Assistant version or detection accuracy in every household.

```sh
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Licensed under the [MIT License](LICENSE).

## Nederlandse uitleg

**WattWatch leert het normale stroomverbruik van apparaten in Home Assistant en signaleert langdurige veranderingen.** De integratie gebruikt bestaande vermogenssensoren van bijvoorbeeld slimme stekkers. Er is geen abonnement of cloudaccount nodig voor WattWatch.

### Installeren

1. Open HACS en voeg via **Aangepaste repositories** deze URL toe: `https://github.com/Kprins1983/Wattwatch`.
2. Kies als type **Integratie**, download WattWatch en herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen → WattWatch**.
4. Klik op **Verzenden** en open daarna het apparaat WattWatch voor het overzicht.

De schermteksten zijn beschikbaar in het Nederlands en Engels. Het bestaande icoon wordt meegeleverd; Home Assistant **2026.3 of nieuwer** ondersteunt dit lokale integratie-icoon. De icoonweergave in HACS hangt ook af van de gebruikte HACS-versie.

### Wat gebeurt er na installatie?

WattWatch zoekt iedere minuut geschikte vermogenssensoren en leert per kanaal het gebruikelijke patroon. De eerste beoordeling vraagt minimaal zeven dagen, 120 bruikbare meeturen en voldoende vergelijkingen op eerdere dagen rond hetzelfde tijdstip. Ontbrekende meetgegevens kunnen dit verlengen. Bestaande Recorder-geschiedenis wordt niet ingelezen.

Na twee opeenvolgende bruikbare uren met dezelfde afwijkingsrichting volgt een melding binnen Home Assistant. Een korte piek is niet het doel; een signaal is geen vastgestelde storing. Telefoon-pushmeldingen zijn in deze versie niet ingebouwd.

### Overzicht en kaarten

Op de apparaatpagina staan **Gevolgde apparaten**, **Afwijkend verbruik** en de statussen per apparaat. Er wordt geen apart dashboard geïnstalleerd.

De vier YAML-voorbeelden hierboven tonen een compact overzicht, leerstatus, vermogensgrafiek en een waarschuwing die alleen bij een afwijking verschijnt. Gebruik **Dashboard bewerken → Kaart toevoegen → Handmatig**. Vervang alle voorbeeld-entiteitsnamen door je eigen namen. Gebruik voor grafieken de oorspronkelijke vermogenssensoren; WattWatch-statussensoren bevatten tekst.

### Instellingen en beperkingen

Via **Configureren** kun je meldingen uitzetten en sensoren uitsluiten of alsnog opnemen. Controleer of de selectie klopt: totaalsensoren en dubbele meetbronnen zijn niet altijd automatisch herkenbaar. WattWatch houdt nog geen rekening met buitentemperatuur, werkdag/weekend of apparaatprogramma's.

Leerdata blijft lokaal en wordt maximaal 21 dagen bewaard. Na een herstart blijft de referentiegeschiedenis behouden; de bevestiging van twee afwijkende uren begint opnieuw. Verwijderen en opnieuw toevoegen laat WattWatch opnieuw leren.

Dit is een testversie. Lees ook [LEESMIJ_EERST.md](LEESMIJ_EERST.md) en [TESTRESULTATEN.md](TESTRESULTATEN.md). De repository is wereldwijd te installeren; opname in de standaard HACS-catalogus vraagt een aparte aanvraag en beoordeling.
