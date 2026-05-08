"""Constants for Life Control MCLH-09 BLE integration."""

from __future__ import annotations

DOMAIN = "life_control_mclh09"
PLATFORMS = ["sensor"]

CONF_DEVICES = "devices"
CONF_MAC = "mac"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_RAW_SOIL = "raw_soil"
CONF_MAX_ATTEMPTS = "max_attempts"

DEFAULT_SCAN_INTERVAL_MINUTES = 10
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RAW_SOIL = False

SERVICE_FORCE_UPDATE = "force_update"
ATTR_ENTRY_ID = "entry_id"
ATTR_MAC = "mac"

MANUFACTURER = "Life Control"
MODEL = "MCLH-09"
