"""Sensors for Life Control MCLH-09 BLE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, CONF_NAME, DOMAIN, MANUFACTURER, MODEL
from .coordinator import MCLH09Coordinator
from .parser import MCLH09State


@dataclass(frozen=True, kw_only=True)
class MCLH09SensorEntityDescription(SensorEntityDescription):
    """MCLH-09 sensor entity description."""

    value_fn: Callable[[MCLH09State], Any]


SENSOR_DESCRIPTIONS: tuple[MCLH09SensorEntityDescription, ...] = (
    MCLH09SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda state: state.temperature,
    ),
    MCLH09SensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda state: state.humidity,
    ),
    MCLH09SensorEntityDescription(
        key="soil",
        translation_key="soil",
        device_class="moisture",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda state: state.soil,
    ),
    MCLH09SensorEntityDescription(
        key="illuminance",
        translation_key="illuminance",
        device_class=SensorDeviceClass.ILLUMINANCE,
        native_unit_of_measurement="lx",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda state: state.illuminance,
    ),
    MCLH09SensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda state: state.battery,
    ),
    MCLH09SensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda state: state.rssi,
    ),
    MCLH09SensorEntityDescription(
        key="failures",
        translation_key="failures",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda state: state.failures,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up MCLH-09 sensors."""
    coordinator: MCLH09Coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[MCLH09Sensor] = []

    for device in coordinator.devices:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(MCLH09Sensor(coordinator, device[CONF_MAC], device[CONF_NAME], description))

    async_add_entities(entities)


class MCLH09Sensor(CoordinatorEntity[MCLH09Coordinator], SensorEntity):
    """Representation of an MCLH-09 sensor entity."""

    entity_description: MCLH09SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MCLH09Coordinator,
        mac: str,
        device_name: str,
        description: MCLH09SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._mac = mac.upper()
        self._device_name = device_name
        self.entity_description = description
        normalized_unique = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"{normalized_unique}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._mac)},
            "connections": {(dr.CONNECTION_BLUETOOTH, self._mac)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self._device_name,
        }

    @property
    def native_value(self) -> Any:
        """Return native sensor value."""
        state = self.coordinator.data.get(self._mac) if self.coordinator.data else None
        if state is None:
            return None
        return self.entity_description.value_fn(state)

    @property
    def available(self) -> bool:
        """Return true when the sensor has a last known value.

        BLE plant sensors may be reachable only intermittently. Keeping the
        last successful value available prevents short read failures from
        turning measurement entities into unavailable and creating gaps in
        Home Assistant history graphs. Read failures are still exposed via the
        diagnostic failures sensor and the last_error attribute.
        """
        state = self.coordinator.data.get(self._mac) if self.coordinator.data else None
        if state is None:
            return False
        if self.entity_description.key == "failures":
            return True
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional diagnostic attributes."""
        state = self.coordinator.data.get(self._mac) if self.coordinator.data else None
        if state is None:
            return {"mac_address": self._mac}

        return {
            "mac_address": self._mac,
            "raw_temperature": state.raw_temperature,
            "raw_humidity": state.raw_humidity,
            "raw_soil": state.raw_soil,
            "raw_illuminance": state.raw_illuminance,
            "last_success": state.last_success.isoformat() if state.last_success else None,
            "last_error": state.last_error,
        }
