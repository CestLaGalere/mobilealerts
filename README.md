# mobilealerts for Home Assistant

integrates home assistant to the mobilealerts sensor reading service

## Documentation

- **[Supported Devices](docs/supported_devices.md)** - Complete list of all supported Mobile Alerts devices and their measurement keys

## Version history

see [Version History](ReleaseHistory.md)

## Installation

To install this integration you will need to add this as a custom repository in HACS.
Open HACS page, then click integrations
Click the three dots top right, select Custom repositories

1. URL enter <https://github.com/cestlagalere/mobilealerts>
2. Category select Integration
3. click Add

Once installed you will then be able to install this integration from the HACS integrations page.

Restart your Home Assistant to complete the installation.

## Configuration

### 🆕 UI-based Configuration (Recommended)

The new version (from v1.4.0) uses Home Assistant's UI for configuration instead of YAML.

#### Step 1: Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **Create Integration** (bottom right)
3. Search for **"mobile_alerts"**
4. Click on **"Mobile Alerts"**
5. Click **Submit** - Done! ✅

#### Step 2: Add Your Devices

After the integration is created:

1. Click the **"Add Entry"** button (top right of the integration card)
2. Enter your device ID (found in Mobile Alerts in your overview, each sensor has an ID: eg. 090005AC99E2)
3. Optionally give a name for your sensor
4. Click **Submit**
5. Your device will now appear in your entities

**Repeat for each device you want to monitor.**

### YAML Configuration (Deprecated but still supported)

You can still use the old YAML configuration, but the devices aren't shwon in the integration device list. You can see the loose entities on tab "Entities".

```yaml
sensor:
  - platform: mobile_alerts
    phone_id: 123456789012
    devices:
      - device_id: 012345678901
        name: Outside Temp
        type: t1
      - device_id: 012345678901
        name: Outside Humidity
        type: h
```

type list:

see [https://mobile-alerts.eu/info/public_server_api_documentation.pdf](https://mobile-alerts.eu/info/public_server_api_documentation.pdf)

| type    | description                                                                                                                                                                  |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| t1      | The measured temperature in celsius.                                                                                                                                         |
| t2      | The measured temperature in celsius of the external sensor / sensor 2.                                                                                                       |
| t3      | The measured temperature in celsius of temperature sensor 3.                                                                                                                 |
| t4      | The measured temperature in celsius of temperature sensor 4.                                                                                                                 |
| h       | The measured humidity.                                                                                                                                                       |
| h1      | The measured humidity of humidity sensor 1.                                                                                                                                  |
| h2      | The measured humidity of humidity sensor 2.                                                                                                                                  |
| h3      | The measured humidity of humidity sensor 3.                                                                                                                                  |
| h4      | The measured humidity of humidity sensor 4.                                                                                                                                  |
| r       | **The rain value in mm (total counter - never resets).** 0.258 mm of rain are equal to one flip. To track rainfall per hour/day/month/year, use Utility Meter (see below). |
| rf      | **The flip count of the rain sensor (total counter - never resets).** A flip equals 0.258 mm of rain. To track rainfall per hour/day/month/year, use Utility Meter (see below). |
| ws      | The measured windspeed in m/s.                                                                                                                                               |
| wg      | The measured gust in m/s.                                                                                                                                                    |
| wd      | The wind direction. 0: N, 1: NNE, 2: NE, 3: ENE, 4: E, 5: ESE, 6: SE, 7: SSE, 8: S, 9: SSW, 10: SW, 11: WSW, 12: W, 13: WNW, 14: NW, 15: NNW. Direction degrees = wd \* 22.5 |
| w       | If the window is opened or closed.                                                                                                                                           |
| h3havg  | Average humidity of the last 3 hours.                                                                                                                                        |
| h24havg | Average humidity of the last 24 hours.                                                                                                                                       |
| h7davg  | Average humidity of the last 7 days.                                                                                                                                         |
| h30davg | Average humidity of the last 30 days.                                                                                                                                        |
| kp1t    | The key press type.                                                                                                                                                          |
| kp1c    | The running counter of key presses.                                                                                                                                          |
| kp2t    | The key press type.                                                                                                                                                          |
| kp2c    | The running counter of key presses.                                                                                                                                          |
| kp3t    | The key press type.                                                                                                                                                          |
| kp3c    | The running counter of key presses.                                                                                                                                          |
| kp4t    | The key press type.                                                                                                                                                          |
| kp4c    | The running counter of key presses.                                                                                                                                          |
| sc      | If the measurement occured because of a status                                                                                                                               |
| ap      | The measured air pressure in hPa.                                                                                                                                            |
| water   | water presence sensor (t2 of MA10350)                                                                                                                                        |

## Measuring Rainfall Per Period (Hourly, Daily, Monthly, Yearly)

The rain sensors (`r` and `rf`) report **total cumulative values** that never reset. To track rainfall for specific periods (hourly, daily, monthly, yearly), use Home Assistant's built-in **Utility Meter** integration.

### Using Utility Meter

The Utility Meter integration converts total counters into period-based measurements automatically.

#### Via YAML Configuration

Add this to your `configuration.yaml`:

```yaml
utility_meter:
  rain_hourly:
    source: sensor.rain_rain_quantity_total        # Your rain sensor entity
    cycle: hourly
    unit_of_measurement: mm

  rain_daily:
    source: sensor.rain_rain_quantity_total
    cycle: daily
    unit_of_measurement: mm

  rain_monthly:
    source: sensor.rain_rain_quantity_total
    cycle: monthly
    unit_of_measurement: mm

  rain_yearly:
    source: sensor.rain_rain_quantity_total
    cycle: yearly
    unit_of_measurement: mm
```

Replace `sensor.rain_rain_quantity_total` with your actual rain sensor entity ID.

#### Via UI (Recommended)

1. Go to **Settings → Automations & Scenes → Helpers**
2. Click **Create Helper → Utility Meter**
3. Select the rain sensor as source
4. Set cycle to "Hourly" (or Daily/Monthly/Yearly)
5. Click **Create**

Repeat for each time period you need.

### Example

After creating the Utility Meter helpers, you'll have new entities:
- `utility_meter.rain_hourly` - Rainfall in the current hour (mm)
- `utility_meter.rain_daily` - Rainfall in the current day (mm)
- `utility_meter.rain_monthly` - Rainfall in the current month (mm)
- `utility_meter.rain_yearly` - Rainfall in the current year (mm)

These values **reset at the period boundary** (hour, day, month, year) and show only the rainfall for that specific period.

For more information, see the [Home Assistant Utility Meter Documentation](https://www.home-assistant.io/integrations/utility_meter/).

## Migration YAML verison to UI Version

Unfortunately we can't migration the ymal configuration entries automatically. But it's very ease to migrate manually. The entity names remain unchanged.

1. Open "Settings --> Devices & service --> Mobile Alerts"
2. Klick on **add entry** and enter your existing device ID and a device name. The device name is new and was not existing in yaml.
3. Klick on **Submit** and you can see an **empty device** (no worries it will work)
4. Repeat from step 2 for other devices
5. Restart Home Assistant and you can see the migrated devices
6. Remove the Mobile Alerts entries from configuration.yaml

## Development

Based on the DataUpdateCoordinator and CoordinatorEntity classes

see [https://developers.home-assistant.io/docs/integration_fetching_data/](https://developers.home-assistant.io/docs/integration_fetching_data/)

raw data can be viewed using

```
curl -d "{'deviceids': 'XXXXXXXXXXXX'}" -H "Content-Type: application/json" https://www.data199.com/api/pv1/device/lastmeasurement
```

If you have a Mobile Alerts device that aren't supported yet (see [List of Supported Devices](docs/supported_devices.md) ), do:

1. Check the [Mobile Alerts website](https://mobile-alerts.eu) for the device model number
2. Open an issue with:
   - Device model number (e.g., MA10XXX)
   - Device name
   - List of measurement keys it provides
   - Device description

You can find the list with the measurement keys for new devices as following:

1. "add entry" and enter the device id as usual
2. Open logs under "Settings --> System --> Logs and search for "(Error) Could not detect device model for device ...".
3. Enter this error message into the opened issue.

For other issues with a known device (addable), do the following:
1. Change log level of HA to `info`. For this open `configuration.yaml` and add this:
```yaml
logger:
  default: info
```
2. Restart HA
3. You should see the API result of Mobile Alerts like this example:
```json
{
  "devices": [
    {
      "deviceid": "XXXXXXXXXXXX",
      "lastseen": 1765662669,
      "lowbattery": false,
      "measurement": {
        "idx": 870953,
        "ts": 1765662668,
        "c": 1765662669,
        "lb": false,
        "t1": 23.3,
        "h": 43.0,
        "ap": 1026.7,
      }
    }
  ]
}
```
4. Send this information to us as an issue. If you send us the real `deviceid` overright it later with `XXXX`.

This information will help us add support for new devices in future versions of the integration.
