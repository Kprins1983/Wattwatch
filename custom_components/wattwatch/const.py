"""WattWatch defaults: no device-specific configuration required."""
DOMAIN = "wattwatch"
NAME = "WattWatch"
VERSION = "0.1.0"
DEFAULTS = {"notifications": True, "excluded": [], "included": []}
PLATFORMS = ["sensor", "binary_sensor"]
