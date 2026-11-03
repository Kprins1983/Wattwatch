"""WattWatch defaults: no device-specific configuration required."""
DOMAIN = "wattwatch"
NAME = "WattWatch"
VERSION = "1.0.1"
DEFAULTS = {"notifications": True, "excluded": [], "included": []}
PLATFORMS = ["sensor", "binary_sensor"]
