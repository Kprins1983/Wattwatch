"""WattWatch defaults: no device-specific configuration required."""
DOMAIN = "wattwatch"
NAME = "WattWatch"
VERSION = "1.1.0"
DEFAULTS = {"sensitivity": "normal", "notifications": True, "excluded": [], "included": []}
PLATFORMS = ["sensor", "binary_sensor"]
