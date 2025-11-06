# Supported Mobile Alerts Devices

This document lists all Mobile Alerts devices supported by this Home Assistant integration. The integration automatically detects the device model based on the measurement data received from the API.

## Device Models

### Temperature Sensors

| Model   | Name                 | Measurement Keys | Description               |
| ------- | -------------------- | ---------------- | ------------------------- |
| MA10100 | Wireless Thermometer | `t1`             | Simple temperature sensor |
| MA10120 | Wireless Thermometer | `t1`             | Simple temperature sensor |

### Temperature & External Temperature Sensors

| Model   | Name                                   | Measurement Keys | Description                             |
| ------- | -------------------------------------- | ---------------- | --------------------------------------- |
| MA10101 | Wireless Thermometer with Cable Sensor | `t1`, `t2`       | Internal and external/cable temperature |

### Thermo-Hygrometers

| Model   | Name                          | Measurement Keys | Description              |
| ------- | ----------------------------- | ---------------- | ------------------------ |
| MA10200 | Wireless Thermo-Hygrometer    | `t1`, `h1`       | Temperature and humidity |
| MA10230 | Wireless Room Climate Station | `t1`, `h1`       | Room climate monitoring  |
| MA10241 | Wireless Thermo-Hygrometer    | `t1`, `h1`       | Temperature and humidity |

### Thermo-Hygrometers with Cable Sensor

| Model             | Name                                           | Measurement Keys | Description                                                              |
| ----------------- | ---------------------------------------------- | ---------------- | ------------------------------------------------------------------------ |
| MA10300 / MA10320 | Wireless Thermo-Hygrometer with Cable Sensor   | `t1`, `t2`, `h1` | Temperature (internal/cable) and humidity                                |
| MA10350           | Wireless Thermo-Hygrometer with Water Detector | `t1`, `t2`, `h1` | Temperature, humidity, and water detection (t2 indicates water presence) |
| MA10700           | Wireless Thermo-Hygrometer with Pool Sensor    | `t1`, `h1`, `t2` | Temperature, humidity, and pool temperature                              |

### Thermo-Hygrometer with Air Pressure

| Model   | Name                          | Measurement Keys | Description                             |
| ------- | ----------------------------- | ---------------- | --------------------------------------- |
| MA10238 | Wireless Air Pressure Monitor | `t1`, `h1`, `ap` | Temperature, humidity, and air pressure |

### Special Sensors

| Model   | Name                         | Measurement Keys | Description          |
| ------- | ---------------------------- | ---------------- | -------------------- |
| MA10450 | Wireless Temperature Station | `h1`             | Humidity sensor only |

### Rain Gauge

| Model   | Name                | Measurement Keys | Description                                                    |
| ------- | ------------------- | ---------------- | -------------------------------------------------------------- |
| MA10650 | Wireless Rain Gauge | `r`, `rf`        | Rainfall measurement in mm and flip counter (0.258mm per flip) |

### Anemometer (Wind Speed)

| Model   | Name                | Measurement Keys | Description                                                                     |
| ------- | ------------------- | ---------------- | ------------------------------------------------------------------------------- |
| MA10660 | Wireless Anemometer | `ws`, `wg`, `wd` | Wind speed, wind gust, wind direction (0-15 = compass direction in 22.5° steps) |

### Contact Sensor

| Model   | Name                    | Measurement Keys | Description                   |
| ------- | ----------------------- | ---------------- | ----------------------------- |
| MA10800 | Wireless Contact Sensor | `w`              | Window/door contact detection |

### Wireless Switch

| Model   | Name            | Measurement Keys                                               | Description                                         |
| ------- | --------------- | -------------------------------------------------------------- | --------------------------------------------------- |
| MA10880 | Wireless Switch | `kp1t`, `kp1c`, `kp2t`, `kp2c`, `kp3t`, `kp3c`, `kp4t`, `kp4c` | 4-channel wireless switch with key press monitoring |

## Measurement Key Reference

- **t1**: Internal/primary temperature sensor (°C)
- **t2**: External/cable temperature sensor (°C) or water detection flag (MA10350)
- **h1**: Relative humidity (%)
- **ap**: Air pressure (hPa)
- **r**: Rainfall accumulated (mm)
- **rf**: Rain flip counter (each flip = 0.258mm)
- **ws**: Wind speed (m/s)
- **wg**: Wind gust (m/s)
- **wd**: Wind direction (0-15 = compass direction in 22.5° steps)
  - 0: N (North), 1: NNE, 2: NE, 3: ENE, 4: E (East), 5: ESE, 6: SE, 7: SSE
  - 8: S (South), 9: SSW, 10: SW, 11: WSW, 12: W (West), 13: WNW, 14: NW, 15: NNW
- **w**: Window/door contact state (0=closed, 1=open)
- **kp\*t**: Key press type for channel (0-3 = different actions)
- **kp\*c**: Key press counter for channel (running counter)
- **lb**: Low battery indicator

## Not Supported

- **MA10870** (Wireless Voltage Monitor) - Measurement keys unknown, not yet supported

If you have such a device, please see chapter "Adding New Devices" and send the log by opening a new issue.

## Automatic Device Detection

When you add a new device in the config flow, the integration automatically:

1. Fetches the latest measurement data from the Mobile Alerts API
2. Analyzes the measurement keys present
3. Identifies the device model based on the measurement combination
4. Displays the device model name in the UI
5. Stores the model information for future use

This automatic detection means you don't need to manually specify the device type - the integration will figure it out for you!

## Adding not supported Devices

If you have a Mobile Alerts device that is not listed here, please:

1. Check the [Mobile Alerts website](https://mobile-alerts.eu) for the device model number
2. Open an issue with:
   - Device model number (e.g., MA10XXX)
   - Device name
   - List of measurement keys it provides
   - Device description

You can find the list with the measurement keys as following:

1. "add entry" and enter the device id as usual
2. Open logs under "Settings --> System --> Logs and search for "(Error) Could not detect device model for device ..." or check "homeassistant.log" with Studio Code Server.
3. Enter this error message into the opened issue.

This information will help us add support for new devices in future versions of the integration.
