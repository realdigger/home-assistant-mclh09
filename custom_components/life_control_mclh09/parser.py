"""Parser and calibration helpers for Life Control MCLH-09 BLE data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import struct

BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
DATA_SERVICE_UUID = "c44cb600-eac7-11e3-acb8-0002a5d5c51b"
DATA_CHAR_UUID = "55482920-eacb-11e3-918a-0002a5d5c51b"

# Current calibration tables ported from dvb6666/esphome-components mclh_09_gateway.
TEMP_INPUT = [1035.0, 909.0, 648.0, 424.0, 368.0, 273.0, 159.0, 0.0]
TEMP_OUTPUT = [68.8, 49.8, 23.7, 6.4, 1.0, -5.5, -20.5, -41.0]

SOIL_INPUT = [1280.0, 1216.0, 1146.0, 1076.0, 1006.0, 936.0, 900.0]
SOIL_OUTPUT = [100.0, 90.28, 70.28, 50.28, 30.28, 10.28, 0.0]

LIGHT_INPUT = [1453.0, 764.0, 741.0, 706.0, 645.0, 545.0, 196.0, 117.0, 24.0, 17.0, 0.0]
LIGHT_OUTPUT = [26700.0, 20700.0, 15700.0, 11700.0, 7700.0, 4000.0, 1500.0, 444.0, 29.0, 17.0, 0.0]


def _limit_value(value: float, min_value: float, max_value: float) -> float:
    return min(max(value, min_value), max_value)


def interpolate(value: float, input_values: list[float], output_values: list[float], limit: bool = False) -> float:
    """Interpolate a raw MCLH-09 sensor value by descending calibration tables."""
    if len(input_values) != len(output_values) or len(input_values) < 3:
        raise ValueError("Bad input/output calibration table size")

    i = 0
    while i < len(input_values) - 2 and value < input_values[i + 1]:
        i += 1

    upper_raw = input_values[i]
    lower_raw = input_values[i + 1]
    upper_out = output_values[i]
    lower_out = output_values[i + 1]

    if upper_raw == lower_raw:
        result = lower_out
    else:
        result = (upper_out - lower_out) * (value - lower_raw) / (upper_raw - lower_raw) + lower_out

    if limit:
        return _limit_value(result, output_values[-1], output_values[0])
    return result


@dataclass(frozen=True)
class MCLH09State:
    """Parsed MCLH-09 state."""

    available: bool
    temperature: float | None = None
    humidity: float | None = None
    soil: float | None = None
    illuminance: float | None = None
    battery: int | None = None
    rssi: int | None = None
    raw_temperature: int | None = None
    raw_humidity: int | None = None
    raw_soil: int | None = None
    raw_illuminance: int | None = None
    failures: int = 0
    last_success: datetime | None = None
    last_error: str | None = None


def parse_sensor_data(data: bytes | bytearray, battery: bytes | bytearray, *, raw_soil_mode: bool) -> dict[str, float | int | None]:
    """Parse the MCLH-09 data characteristic.

    Known payload layout used by the ESPHome component:
      0..1: raw temperature, uint16 little-endian
      2..3: raw air humidity, uint16 little-endian, value / 13
      4..5: raw soil moisture, uint16 little-endian
      6..7: raw illuminance, uint16 little-endian

    Some older examples only handled 6 bytes; this parser accepts both layouts.
    """
    payload = bytes(data)
    if len(payload) < 6:
        raise ValueError(f"MCLH-09 data payload is too short: {len(payload)} bytes")

    if len(payload) >= 8:
        raw_temp, raw_humidity, raw_soil, raw_light = struct.unpack_from("<HHHH", payload, 0)
        humidity: float | None = round(raw_humidity / 13.0, 1)
    else:
        raw_temp, raw_soil, raw_light = struct.unpack_from("<HHH", payload, 0)
        raw_humidity = None
        humidity = None

    battery_payload = bytes(battery)
    battery_level = battery_payload[0] if battery_payload else None

    soil_value: float | int = raw_soil if raw_soil_mode else interpolate(float(raw_soil), SOIL_INPUT, SOIL_OUTPUT, limit=True)

    return {
        "temperature": round(interpolate(float(raw_temp), TEMP_INPUT, TEMP_OUTPUT), 1),
        "humidity": humidity,
        "soil": round(soil_value, 0) if not raw_soil_mode else raw_soil,
        "illuminance": round(interpolate(float(raw_light), LIGHT_INPUT, LIGHT_OUTPUT), 0),
        "battery": battery_level,
        "raw_temperature": raw_temp,
        "raw_humidity": raw_humidity,
        "raw_soil": raw_soil,
        "raw_illuminance": raw_light,
    }
