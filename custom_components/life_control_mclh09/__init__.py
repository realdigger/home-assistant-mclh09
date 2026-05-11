"""Life Control MCLH-09 BLE integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import ATTR_ENTRY_ID, ATTR_MAC, DOMAIN, PLATFORMS, SERVICE_FORCE_UPDATE
from .coordinator import MCLH09Coordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_FORCE_UPDATE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_MAC): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Life Control MCLH-09 BLE from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = MCLH09Coordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _async_register_services(hass)

    # Do not block config entry setup with active BLE/GATT reads.
    # Polling several sensors can take longer than Home Assistant's setup
    # watchdog timeout when devices are far away or temporarily unreachable.
    # Entities are created immediately, and the first refresh runs in the
    # background; the last-known-value logic keeps entities stable after the
    # first successful read.
    refresh_task = hass.async_create_task(
        coordinator.async_request_refresh(),
        name=f"{DOMAIN}_{entry.entry_id}_initial_refresh",
    )
    entry.async_on_unload(refresh_task.cancel)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_FORCE_UPDATE)
            hass.data.pop(DOMAIN)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_FORCE_UPDATE):
        return

    async def _handle_force_update(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_ENTRY_ID)
        mac = call.data.get(ATTR_MAC)
        coordinators: dict[str, MCLH09Coordinator] = hass.data.get(DOMAIN, {})

        if entry_id:
            coordinator = coordinators.get(entry_id)
            if coordinator is None:
                raise vol.Invalid(f"Unknown {DOMAIN} entry_id: {entry_id}")
            await coordinator.async_force_update(mac)
            return

        if mac:
            normalized = mac.upper()
            matches = [coordinator for coordinator in coordinators.values() if coordinator.has_address(normalized)]
            if not matches:
                raise vol.Invalid(f"MAC address {mac} is not configured")
            for coordinator in matches:
                await coordinator.async_force_update(normalized)
            return

        for coordinator in coordinators.values():
            await coordinator.async_force_update()

    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_UPDATE,
        _handle_force_update,
        schema=SERVICE_FORCE_UPDATE_SCHEMA,
    )
