# Home Assistant MCLH-09 BLE

Custom Home Assistant integration for reading data from Life Control MCLH-09 BLE plant sensors.

The integration allows you to add multiple BLE MAC addresses and periodically read sensor data from each device.

## Features

- Multiple Life Control MCLH-09 devices
- Active BLE polling
- Temperature sensor
- Air humidity sensor
- Soil moisture sensor
- Light level sensor
- Battery sensor
- RSSI sensor
- BLE read error counter
- Manual update service
- Optional raw soil moisture value

## Requirements

- Home Assistant with Bluetooth support
- A Bluetooth adapter supported by Home Assistant, or an ESPHome Bluetooth Proxy
- Life Control MCLH-09 BLE plant sensor devices

For reliable operation, an ESPHome Bluetooth Proxy placed close to the sensors is recommended.

## Installation

### Manual installation

Copy the integration folder:

```text
custom_components/life_control_mclh09
```

to your Home Assistant configuration directory:

```text
/config/custom_components/life_control_mclh09
```

Then restart Home Assistant.

### HACS custom repository

After publishing this repository on GitHub, it can be added to HACS as a custom repository:

```text
HACS → Integrations → Custom repositories
```

Repository URL:

```text
https://github.com/realdigger/home-assistant-mclh09/
```

Category:

```text
Integration
```

## Configuration

After installation and restart:

```text
Settings → Devices & services → Add integration → Life Control MCLH-09 BLE
```

Add one or more devices using their BLE MAC addresses.

Example:

```text
AA:BB:CC:DD:EE:FF; Ficus
11:22:33:44:55:66; Orchid
```

You can also specify only the MAC address:

```text
AA:BB:CC:DD:EE:FF
```

In that case, the integration will generate a default device name.

## Device address format

Each line contains one device.

Supported formats:

```text
MAC_ADDRESS
MAC_ADDRESS; Device name
```

Examples:

```text
AA:BB:CC:DD:EE:FF
AA:BB:CC:DD:EE:FF; Kitchen plant
```

## Services

### Force update

The integration provides a service for forcing an immediate data refresh:

```yaml
service: life_control_mclh09.force_update
```

## Notes

Life Control MCLH-09 devices are read using active BLE polling. This means Home Assistant needs to establish a BLE connection to each device during every update cycle.

Because BLE connections are limited and can be unstable depending on adapter quality, distance, interference, and proxy placement, avoid using very short polling intervals when adding many devices.

Recommended initial polling interval:

```text
5–10 minutes
```

## Troubleshooting

### Device does not update

Check the following:

- The MAC address is correct.
- The device is within Bluetooth range.
- The battery is not empty.
- Home Assistant Bluetooth is working.
- ESPHome Bluetooth Proxy is online, if used.
- The update interval is not too short for the number of devices.

### Some devices update, others fail

This is usually caused by BLE connection limits, weak signal, or polling too frequently. Increase the update interval or add another Bluetooth Proxy closer to the sensors.

### RSSI is low

Move the Bluetooth adapter or ESPHome Bluetooth Proxy closer to the sensor.

## Repository

GitHub repository:

```text
https://github.com/realdigger/home-assistant-mclh09/
```

Home Assistant integration domain:

```text
life_control_mclh09
```

## Credits

Parts of the BLE protocol handling were implemented with reference to:

```text
https://github.com/dvb6666/esphome-components
```

## License

This project is licensed under the GNU General Public License v3.0.

Parts of the BLE protocol handling were implemented with reference to
dvb6666/esphome-components, which is also licensed under GPL-3.0.
