"""Config flow for Life Control MCLH-09 BLE integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_DEVICES,
    CONF_MAC,
    CONF_MAX_ATTEMPTS,
    CONF_NAME,
    CONF_RAW_SOIL,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_RAW_SOIL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)

MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


def normalize_mac(mac: str) -> str:
    """Normalize MAC address to AA:BB:CC:DD:EE:FF."""
    value = mac.strip().replace("-", ":").upper()
    if not MAC_RE.match(value):
        raise ValueError(f"Invalid MAC address: {mac}")
    return value


def parse_devices(raw: str) -> list[dict[str, str]]:
    """Parse multiline device list.

    Supported line formats:
      AA:BB:CC:DD:EE:FF
      AA:BB:CC:DD:EE:FF; Living room
      Living room; AA:BB:CC:DD:EE:FF
    Comma may be used instead of semicolon.
    """
    devices: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in re.split(r"[;,]", line, maxsplit=1) if part.strip()]
        if len(parts) == 1:
            mac = normalize_mac(parts[0])
            name = f"MCLH-09 {mac[-5:].replace(':', '')}"
        elif len(parts) == 2:
            if MAC_RE.match(parts[0].replace("-", ":")):
                mac = normalize_mac(parts[0])
                name = parts[1]
            elif MAC_RE.match(parts[1].replace("-", ":")):
                name = parts[0]
                mac = normalize_mac(parts[1])
            else:
                raise ValueError(f"Line does not contain a valid MAC address: {line}")
        else:
            raise ValueError(f"Bad device line: {line}")

        if mac in seen:
            raise ValueError(f"Duplicate MAC address: {mac}")
        seen.add(mac)
        devices.append({CONF_MAC: mac, CONF_NAME: name or f"MCLH-09 {mac[-5:].replace(':', '')}"})

    if not devices:
        raise ValueError("Add at least one device")
    return devices


def devices_to_text(devices: list[dict[str, str]]) -> str:
    """Convert stored devices to multiline text for config/options UI."""
    return "\n".join(f"{device[CONF_MAC]}; {device[CONF_NAME]}" for device in devices)


def build_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build config/options form schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_DEVICES, default=defaults.get(CONF_DEVICES, "")): str,
            vol.Required(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
            vol.Required(CONF_MAX_ATTEMPTS, default=defaults.get(CONF_MAX_ATTEMPTS, DEFAULT_MAX_ATTEMPTS)): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Required(CONF_RAW_SOIL, default=defaults.get(CONF_RAW_SOIL, DEFAULT_RAW_SOIL)): bool,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Life Control MCLH-09 BLE."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                devices = parse_devices(user_input[CONF_DEVICES])
            except ValueError:
                errors[CONF_DEVICES] = "invalid_devices"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Life Control MCLH-09 BLE",
                    data={
                        CONF_DEVICES: devices,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_MAX_ATTEMPTS: user_input[CONF_MAX_ATTEMPTS],
                        CONF_RAW_SOIL: user_input[CONF_RAW_SOIL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options for Life Control MCLH-09 BLE."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}

        current = dict(self.config_entry.data)
        current.update(self.config_entry.options)
        defaults = dict(current)
        defaults[CONF_DEVICES] = devices_to_text(current[CONF_DEVICES])

        if user_input is not None:
            try:
                devices = parse_devices(user_input[CONF_DEVICES])
            except ValueError:
                errors[CONF_DEVICES] = "invalid_devices"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_DEVICES: devices,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_MAX_ATTEMPTS: user_input[CONF_MAX_ATTEMPTS],
                        CONF_RAW_SOIL: user_input[CONF_RAW_SOIL],
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=build_schema(defaults),
            errors=errors,
        )
