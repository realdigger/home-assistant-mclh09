# Life Control MCLH-09 BLE for Home Assistant

Custom integration for reading Life Control MCLH-09 BLE plant sensors directly from Home Assistant.

## Features

- Multiple MCLH-09 BLE MAC addresses in one integration entry.
- Active GATT polling.
- Sensors per device:
  - temperature
  - air humidity
  - soil moisture
  - illuminance
  - battery
  - RSSI
  - BLE read failures
- Optional raw soil reading instead of calibrated percent.
- Service `life_control_mclh09.force_update`.

## Installation

Copy the folder:

```text
custom_components/life_control_mclh09
```

to:

```text
/config/custom_components/life_control_mclh09
```

Restart Home Assistant.

## Setup

1. Make sure the built-in Home Assistant Bluetooth integration works.
2. For stable reads, use an ESPHome Bluetooth Proxy near the MCLH-09 sensors.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Life Control MCLH-09 BLE**.
5. Add devices, one per line:

```text
AA:BB:CC:DD:EE:FF; Basil
11:22:33:44:55:66; Orchid
```

Supported line formats:

```text
AA:BB:CC:DD:EE:FF
AA:BB:CC:DD:EE:FF; Name
Name; AA:BB:CC:DD:EE:FF
```

## Force update service

```yaml
service: life_control_mclh09.force_update
```

One device:

```yaml
service: life_control_mclh09.force_update
data:
  mac: "AA:BB:CC:DD:EE:FF"
```

## Notes

The parser and calibration tables are ported from the ESPHome MCLH-09 gateway implementation by dvb6666.

## Brand images

The package includes local Home Assistant brand images in `custom_components/life_control_mclh09/brand/`.
