"""Conservative automatic selection. No universally reliable meter-role metadata exists."""
import re

# Boundaries avoid excluding e.g. a solar boiler or heat pump by substring.
EXCLUDE = re.compile(
    r"(^|[\W_])(p1|nexus|inverter|pv\d*|solar|zonnepanelen|thuisbatterij|"
    r"batterij|battery|fase|phase|l[123]|totaal|total|grid|netmeter|"
    r"import|export|production|productie|teruglevering|reclaimed|teruggewonnen)([\W_]|$)",
    re.I,
)
AGGREGATE = re.compile(
    r"werkelijk.*huisverbruik|house_consumption|current_usage|connect_energiemeter|"
    r"power_production_now|pv[12]_power|goodwe_meter_active_power|"
    r"(^|[\W_])(huisverbruik|netvermogen|net_import|net_export)([\W_]|$)", re.I)


def select(candidates, included=(), excluded=()):
    """Return selected IDs and explicit reasons for every rejected candidate.

    Candidates have id, name, unit, device_class, device_id, platform, disabled.
    Only collapse duplicate power channels on the SAME known device; keep
    named channels so a multi-socket strip can expose distinct outlets.
    """
    selected, rejected = [], {}
    groups = {}
    for item in sorted(candidates, key=lambda i: i["id"]):
        eid = item["id"]
        if item.get("platform") == "wattwatch" or item.get("disabled"):
            continue
        if item.get("unit") not in ("W", "kW", "mW"):
            continue
        if item.get("device_class") not in (None, "power"):
            continue
        if eid in excluded:
            rejected[eid] = "manually_excluded"
        elif eid not in included and (EXCLUDE.search(eid + " " + item.get("name", ""))
                                     or AGGREGATE.search(eid)):
            rejected[eid] = "meter_or_generation"
        else:
            # Only obvious identical channel aliases. Do not deduplicate all
            # sensors with a device_id: that would drop multi-channel devices.
            channel = re.sub(r"(_power|_vermogen|_electric_power)(?:_\d+)?$", "", eid.split(".", 1)[-1])
            key = (item.get("device_id"), channel)
            if key[0] and key in groups and eid not in included:
                rejected[eid] = "duplicate_of:" + groups[key]
            else:
                groups[key] = eid
                selected.append(eid)
    return selected, rejected
