"""BLE reader for Life Control MCLH-09."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .parser import BATTERY_UUID, DATA_CHAR_UUID, MCLH09State, parse_sensor_data

_LOGGER = logging.getLogger(__name__)
CONNECT_TIMEOUT = 15.0
READ_TIMEOUT = 10.0


class MCLH09ReadError(Exception):
    """Raised when an MCLH-09 device cannot be read."""


async def async_read_device(
    hass: HomeAssistant,
    *,
    address: str,
    name: str,
    raw_soil_mode: bool,
    max_attempts: int,
    previous_failures: int = 0,
) -> MCLH09State:
    """Connect to an MCLH-09 sensor and read battery + measurement data."""
    address = address.upper()
    service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
    rssi = service_info.rssi if service_info is not None else None

    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise MCLH09ReadError(f"BLE device {address} is not currently reachable by a connectable adapter/proxy")

    client = None
    try:
        client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            name,
            max_attempts=max_attempts,
            timeout=CONNECT_TIMEOUT,
            ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
                hass, address, connectable=True
            ),
        )

        battery = await asyncio.wait_for(client.read_gatt_char(BATTERY_UUID), timeout=READ_TIMEOUT)
        data = await asyncio.wait_for(client.read_gatt_char(DATA_CHAR_UUID), timeout=READ_TIMEOUT)

        parsed = parse_sensor_data(data, battery, raw_soil_mode=raw_soil_mode)
        return MCLH09State(
            available=True,
            rssi=rssi,
            failures=previous_failures,
            last_success=dt_util.utcnow(),
            **parsed,
        )

    except (asyncio.TimeoutError, BleakError, OSError, ValueError) as err:
        raise MCLH09ReadError(str(err)) from err
    finally:
        if client is not None:
            try:
                await client.disconnect()
            except Exception as err:  # noqa: BLE001 - disconnect errors must not hide read result
                _LOGGER.debug("Error while disconnecting from %s: %s", address, err)
        try:
            bluetooth.async_clear_advertisement_history(hass, address)
        except Exception as err:  # noqa: BLE001 - compatibility with older HA versions
            _LOGGER.debug("Could not clear advertisement history for %s: %s", address, err)
