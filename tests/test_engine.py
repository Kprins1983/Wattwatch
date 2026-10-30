"""Behavioral tests, including failures that could generate false alarms."""
import importlib.util
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest

ROOT = Path(__file__).parents[1] / "custom_components/wattwatch"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


engine, discovery = module("engine"), module("discovery")
BASE = 1735689600  # 2025-01-01 00:00 UTC


def trained(power=100):
    p = engine.Profile(first_seen=BASE)
    for i in range(8 * 24):
        stamp = BASE + i * 3600
        date = datetime.fromtimestamp(stamp, timezone.utc)
        p.history.append({"start": stamp, "hour": date.hour,
                          "day": date.date().isoformat(), "watts": power})
    return p


def feed(p, start, minutes, value):
    results = []
    for i in range(minutes):
        stamp = start + 60 * i
        date = datetime.fromtimestamp(stamp, timezone.utc)
        result = p.sample(stamp, value(i) if callable(value) else value,
                          date.hour, date.date().isoformat())
        if result:
            results.append(result)
    return results


@pytest.mark.parametrize("value,unit,expected", [(".25", "kW", 250), ("500", "mW", .5),
    ("unknown", "W", None), ("unavailable", "W", None), ("nan", "W", None),
    ("inf", "W", None), (-1, "W", None), (3, "kWh", None)])
def test_power_validation(value, unit, expected):
    assert engine.watts(value, unit) == expected


def test_sustained_high_only_after_two_hours_and_not_learned():
    p = trained()
    results = feed(p, BASE + 8 * 86400, 121, 200)
    assert [r["status"] for r in results] == ["normal", "anomaly"]
    assert results[-1]["direction"] == "high"
    assert len(p.history) == 192  # No adaptation toward the fault.


def test_sustained_low_and_recovery():
    p = trained()
    results = feed(p, BASE + 8 * 86400, 121, 0)
    assert results[-1]["direction"] == "low" and p.anomaly
    feed(p, BASE + 8 * 86400 + 121 * 60, 120, 100)
    assert not p.anomaly


def test_short_peak_does_not_trigger():
    p = trained()
    feed(p, BASE + 8 * 86400, 181, lambda i: 2000 if i == 10 else 100)
    assert not p.anomaly
    assert p.candidate == ""


def test_regular_washing_cycles_are_inside_learned_envelope():
    p = trained(0)
    for index, record in enumerate(p.history):
        record["watts"] = 700 if index % 48 < 2 else 0
    results = feed(p, BASE + 8 * 86400, 121, 700)
    assert all(r["status"] == "normal" for r in results)


def test_outage_not_counted_as_zero_and_breaks_confirmation():
    p = trained()
    feed(p, BASE + 8 * 86400, 61, 250)
    assert p.consecutive == 1
    feed(p, BASE + 8 * 86400 + 61 * 60, 120, None)
    assert not p.anomaly and p.consecutive == 0
    assert p.status(BASE + 9 * 86400) == "unavailable"


def test_restart_keeps_history_but_never_integrates_downtime():
    p = trained()
    feed(p, BASE + 8 * 86400, 61, 200)
    restored = engine.Profile.load(p.dump())
    assert restored.history == p.history
    assert restored.previous_time is None and restored.consecutive == 0
    results = feed(restored, BASE + 9 * 86400, 61, 200)
    assert results[-1]["status"] == "normal"  # Confirmation starts over.


def test_cold_start_full_learning_period_and_hourly_weighting():
    p = engine.Profile()
    results = feed(p, BASE, 7 * 24 * 60, lambda i: 80 if i % 60 < 30 else 120)
    assert all(r["status"] == "learning" for r in results)
    assert all(abs(r["watts"] - 100) < .01 for r in p.history)
    result = feed(p, BASE + 7 * 86400, 1, 80)[0]
    assert result["status"] == "normal"
    assert p.progress(BASE + 7 * 86400) == 100


def test_long_sampling_gap_does_not_fake_full_hour():
    p = trained()
    feed(p, BASE + 8 * 86400, 2, 100)
    result = feed(p, BASE + 8 * 86400 + 3600, 1, 900)
    assert result == [] and not p.anomaly
    assert p.last_evaluation["status"] == "insufficient_data"


def item(eid, device="device", **kwargs):
    return {"id": "sensor." + eid, "name": eid, "unit": "W", "device_id": device,
            "device_class": "power", **kwargs}


def test_discovery_excludes_meters_keeps_appliances_and_new_channels():
    candidates = [item(n) for n in ["p1_meter_vermogen", "nexus_vermogen_2", "pv_power_2",
        "droger_power", "warmtepomp_vermogen_2", "zonneboiler_1_power", "stekker_1_power",
        "stekker_2_power"]]
    selected, rejected = discovery.select(candidates)
    assert set(selected) == {"sensor." + n for n in ["droger_power", "warmtepomp_vermogen_2",
        "zonneboiler_1_power", "stekker_1_power", "stekker_2_power"]}
    assert len(rejected) == 3


def test_explicit_override_and_exclusion_precedence():
    candidates = [item("grid_power"), item("lamp_power")]
    selected, _ = discovery.select(candidates, ["sensor.grid_power"], ["sensor.lamp_power"])
    assert selected == ["sensor.grid_power"]
    selected, _ = discovery.select(candidates, ["sensor.grid_power"], ["sensor.grid_power"])
    assert selected == ["sensor.lamp_power"]


def test_duplicate_aliases_but_not_multichannel_devices():
    selected, rejected = discovery.select([item("plug_power"), item("plug_vermogen"),
                                           item("plug_channel_2_power")])
    assert len(selected) == 2 and len(rejected) == 1


def test_excludes_own_entities_and_non_power():
    selected, _ = discovery.select([item("self", platform="wattwatch"),
                                   item("energy", unit="kWh"),
                                   item("disabled", disabled=True)])
    assert selected == []
