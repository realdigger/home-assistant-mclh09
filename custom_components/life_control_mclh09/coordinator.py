"""Data coordinator for Life Control MCLH-09 BLE devices."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble import MCLH09ReadError, async_read_device
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
from .parser import MCLH09State

_LOGGER = logging.getLogger(__name__)


def entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return config entry data with options applied."""
    merged = dict(entry.data)
    merged.update(entry.options)
    return merged


class MCLH09Coordinator(DataUpdateCoordinator[dict[str, MCLH09State]]):
    """Coordinator that polls all configured MCLH-09 BLE devices sequentially."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        cfg = entry_config(entry)
        self.devices: list[dict[str, str]] = cfg[CONF_DEVICES]
        self.raw_soil_mode: bool = cfg.get(CONF_RAW_SOIL, DEFAULT_RAW_SOIL)
        self.max_attempts: int = cfg.get(CONF_MAX_ATTEMPTS, DEFAULT_MAX_ATTEMPTS)
        interval_minutes: int = cfg.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
        self._update_lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    def has_address(self, address: str) -> bool:
        """Return true if address belongs to this coordinator."""
        normalized = address.upper()
        return any(device[CONF_MAC].upper() == normalized for device in self.devices)

    async def _async_update_data(self) -> dict[str, MCLH09State]:
        """Poll all configured devices."""
        async with self._update_lock:
            return await self._async_read_many(self.devices)

    async def async_force_update(self, address: str | None = None) -> None:
        """Force immediate update of all devices or a single MAC address."""
        async with self._update_lock:
            if address is None:
                data = await self._async_read_many(self.devices)
            else:
                normalized = address.upper()
                device = next((item for item in self.devices if item[CONF_MAC].upper() == normalized), None)
                if device is None:
                    raise ValueError(f"MAC address {address} is not configured in this entry")
                data = dict(self.data or {})
                data[normalized] = await self._async_read_one(device)
            self.async_set_updated_data(data)

    async def _async_read_many(self, devices: list[dict[str, str]]) -> dict[str, MCLH09State]:
        result: dict[str, MCLH09State] = dict(self.data or {})
        for index, device in enumerate(devices):
            mac = device[CONF_MAC].upper()
            result[mac] = await self._async_read_one(device)
            if index < len(devices) - 1:
                await asyncio.sleep(0.5)
        return result

    async def _async_read_one(self, device: dict[str, str]) -> MCLH09State:
        mac = device[CONF_MAC].upper()
        previous = (self.data or {}).get(mac)
        previous_failures = previous.failures if previous else 0
        try:
            return await async_read_device(
                self.hass,
                address=mac,
                name=device[CONF_NAME],
                raw_soil_mode=self.raw_soil_mode,
                max_attempts=self.max_attempts,
                previous_failures=previous_failures,
            )
        except MCLH09ReadError as err:
            failures = previous_failures + 1
            _LOGGER.debug("Failed to read MCLH-09 %s (%s): %s", device[CONF_NAME], mac, err)
            if previous is not None:
                return replace(previous, available=False, failures=failures, last_error=str(err))
            return MCLH09State(available=False, failures=failures, last_error=str(err))
