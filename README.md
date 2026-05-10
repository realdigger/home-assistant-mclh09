# Life Control MCLH-09 BLE

[![GitHub release](https://img.shields.io/github/v/release/realdigger/home-assistant-mclh09)](https://github.com/realdigger/home-assistant-mclh09/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Unofficial Home Assistant custom integration for **Life Control MCLH-09 BLE** plant sensors.

## Features

- Support for multiple MCLH-09 sensors in a single config entry
- Temperature sensor
- Air humidity sensor
- Soil moisture sensor
- Illuminance sensor
- Battery level sensor
- RSSI sensor
- BLE read error counter
- Service for forced polling
- Optional raw soil moisture mode

## Supported devices

- Life Control MCLH-09 BLE plant sensor

Tested data points:

- Temperature
- Air humidity
- Soil moisture
- Illuminance
- Battery level
- RSSI

## Requirements

- Home Assistant
- Bluetooth integration enabled
- A working local Bluetooth adapter **or** ESPHome Bluetooth Proxy
- For best stability, ESPHome Bluetooth Proxy is recommended

## Installation

### Option 1 — HACS

1. Open **HACS**.
2. Go to **Integrations**.
3. Add a custom repository:
   - **Repository**: `https://github.com/realdigger/home-assistant-mclh09`
   - **Category**: `Integration`
4. Search for **Life Control MCLH-09 BLE**.
5. Install the integration.
6. Restart Home Assistant.

### Option 2 — Manual

1. Copy the `custom_components/life_control_mclh09` directory into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & Services**.

## Configuration

When adding the integration, enter one or more BLE MAC addresses.

### Device list example

```text
00:1B:DC:4B:12:25; plant1
00:1B:DC:4B:15:04; plant4
```

One device per line.

Supported formats:

```text
AA:BB:CC:DD:EE:FF
AA:BB:CC:DD:EE:FF;
AA:BB:CC:DD:EE:FF; Name
AA:BB:CC:DD:EE:FF; Name;
```

Available options:

- **Polling interval, minutes**
- **BLE connection retries**
- **Publish raw soil moisture value instead of percentage**

## Bluetooth Proxy

For reliable operation, **ESPHome Bluetooth Proxy with active BLE connections** is recommended.

The proxy must support active GATT connections:

```yaml
bluetooth_proxy:
  active: true
```

Passive BLE scanning is not enough for this integration.

Example ESPHome fragment:

```yaml
esp32_ble:
  max_connections: 5
  connection_timeout: 20s

esp32_ble_tracker:
  scan_parameters:
    active: true

bluetooth_proxy:
  active: true
  cache_services: true
  connection_slots: 5
```

## Services

### `life_control_mclh09.force_update`

Force immediate polling of all configured devices.

Example:

```yaml
service: life_control_mclh09.force_update
```

Depending on the installed version of the integration, the service may also support a MAC/address field for polling a specific sensor.

## Known limitations

- The sensor must be reachable over BLE during the polling cycle.
- Weak RSSI may cause intermittent read errors.
- RSSI around `-80 dBm` or worse may be unstable for active BLE reads.
- BLE reliability depends on adapter quality, distance, and radio environment.

## Troubleshooting

### Sensors are unavailable

Check that:

- The Bluetooth adapter or ESPHome Bluetooth Proxy is online.
- The proxy shows support for active connections in Home Assistant.
- The sensor is close enough to the adapter/proxy.
- The configured MAC address is correct.
- The Bluetooth integration in Home Assistant is working.

### Bluetooth Proxy only receives advertisements

The ESPHome YAML must include:

```yaml
bluetooth_proxy:
  active: true
```

You should see active connections support in Home Assistant Bluetooth adapters.

### Data appears, but the BLE read error counter is high

Move the Bluetooth adapter or ESPHome Bluetooth Proxy closer to the sensor and check RSSI.

### The integration is not offered for setup

Make sure:

- `custom_components/life_control_mclh09` exists
- `manifest.json` is valid
- Home Assistant has been restarted after installation

## Debug logging

Add this to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.life_control_mclh09: debug
    bleak_retry_connector: debug
    homeassistant.components.bluetooth: debug
```

Then restart Home Assistant and inspect the logs.

## Disclaimer

This is an unofficial Home Assistant custom integration for Life Control MCLH-09 BLE plant sensors.

This project is not affiliated with, endorsed by, sponsored by, or approved by Life Control or its trademark owners.

All product names, trademarks, and registered trademarks are the property of their respective owners and are used only to identify compatible devices.

## Credits

Parts of the BLE protocol handling were implemented with reference to:

- [dvb6666/esphome-components](https://github.com/dvb6666/esphome-components)

## License

This project is licensed under the GNU General Public License v3.0.

Parts of the BLE protocol handling were implemented with reference to
dvb6666/esphome-components, which is also licensed under GPL-3.0.
