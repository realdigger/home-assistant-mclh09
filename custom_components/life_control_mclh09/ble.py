"""BLE reader for Life Control MCLH-09."""

from __future__ import annotations

import asyncio
import logging

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .parser import BATTERY_UUID, DATA_CHAR_UUID, MCLH09State, parse_sensor_data

_LOGGER = logging.getLogger(__name__)
CONNECT_TIMEOUT = 20.0
READ_TIMEOUT = 15.0
POST_CONNECT_DELAY = 1.0
READ_BETWEEN_DELAY = 0.3


class MCLH09ReadError(Exception):
    """Raised when an MCLH-09 device cannot be read."""


def _hex(payload: bytes | bytearray | None) -> str:
    """Format bytes for debug logs."""
    if payload is None:
        return "<none>"
    return bytes(payload).hex(" ").upper()


def _log_services(client: BleakClientWithServiceCache, address: str) -> None:
    """Log discovered GATT services and characteristics."""
    if not _LOGGER.isEnabledFor(logging.DEBUG):
        return

    try:
        services = client.services
    except Exception as err:  # noqa: BLE001 - diagnostic only
        _LOGGER.debug("Could not get GATT services for %s: %s", address, err)
        return

    if not services:
        _LOGGER.debug("No GATT services available for %s", address)
        return

    for service in services:
        _LOGGER.debug("%s GATT service: %s", address, service.uuid)
        for char in service.characteristics:
            _LOGGER.debug(
                "%s   characteristic: %s properties=%s handle=%s",
                address,
                char.uuid,
                list(char.properties),
                getattr(char, "handle", None),
            )


def _find_characteristic(client: BleakClientWithServiceCache, uuid: str):
    """Find a characteristic object by UUID, ignoring case and dashes."""
    wanted = uuid.replace("-", "").lower()
    try:
        services = client.services
    except Exception:  # noqa: BLE001 - fallback path
        return uuid

    if not services:
        return uuid

    for service in services:
        for char in service.characteristics:
            if char.uuid.replace("-", "").lower() == wanted:
                return char
    return uuid


async def _read_optional_char(
    client: BleakClientWithServiceCache,
    *,
    address: str,
    uuid: str,
    label: str,
) -> bytes | None:
    """Read an optional GATT characteristic and return None on failure."""
    try:
        char = _find_characteristic(client, uuid)
        payload = await asyncio.wait_for(client.read_gatt_char(char), timeout=READ_TIMEOUT)
        _LOGGER.debug("%s read %s %s: %s", address, label, uuid, _hex(payload))
        return bytes(payload)
    except (asyncio.TimeoutError, BleakError, OSError) as err:
        _LOGGER.debug("%s could not read optional %s %s: %s", address, label, uuid, err)
        return None


async def _read_required_char(
    client: BleakClientWithServiceCache,
    *,
    address: str,
    uuid: str,
    label: str,
) -> bytes:
    """Read a required GATT characteristic."""
    char = _find_characteristic(client, uuid)
    payload = await asyncio.wait_for(client.read_gatt_char(char), timeout=READ_TIMEOUT)
    _LOGGER.debug("%s read %s %s: %s", address, label, uuid, _hex(payload))
    return bytes(payload)


async def async_read_device(
    hass: HomeAssistant,
    *,
    address: str,
    name: str,
    raw_soil_mode: bool,
    max_attempts: int,
    previous_failures: int = 0,
) -> MCLH09State:
    """Connect to an MCLH-09 sensor and read measurement data."""
    address = address.upper()
    service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
    rssi = service_info.rssi if service_info is not None else None

    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise MCLH09ReadError(f"BLE device {address} is not currently reachable by a connectable adapter/proxy")

    _LOGGER.debug(
        "Reading MCLH-09 %s (%s), rssi=%s, attempts=%s, source=%s",
        name,
        address,
        rssi,
        max_attempts,
        getattr(service_info, "source", None) if service_info is not None else None,
    )

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

        _LOGGER.debug("Connected to MCLH-09 %s (%s)", name, address)
        await asyncio.sleep(POST_CONNECT_DELAY)
        _log_services(client, address)

        # Battery is useful, but it must not block the main measurements.
        # Some devices/proxies expose the custom data characteristic reliably while
        # battery read may intermittently fail.
        battery = await _read_optional_char(client, address=address, uuid=BATTERY_UUID, label="battery")
        await asyncio.sleep(READ_BETWEEN_DELAY)
        data = await _read_required_char(client, address=address, uuid=DATA_CHAR_UUID, label="data")

        parsed = parse_sensor_data(data, battery or b"", raw_soil_mode=raw_soil_mode)
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
