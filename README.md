# mobilealerts for Home Assistant

integrates home assistant to the mobilealerts sensor reading service

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

add elements to yaml sensor section:
```
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

type:

see [https://mobile-alerts.eu/info/public_server_api_documentation.pdf](https://mobile-alerts.eu/info/public_server_api_documentation.pdf)

type | description |
| --- | --- |
| t1 | The measured temperature in celsius. |
| t2 | The measured temperature in celsius of the external sensor / sensor 2. |
| t3 | The measured temperature in celsius of temperature sensor 3. |
| t4 | The measured temperature in celsius of temperature sensor 4. |
| h | The measured humidity. |
| h1 | The measured humidity of humidity sensor 1. |
| h2 | The measured humidity of humidity sensor 2. |
| h3 | The measured humidity of humidity sensor 3. |
| h4 | The measured humidity of humidity sensor 4. |
| r | The rain value in mm. 0.258 mm of rain are equal to one flip. |
| rf | The flip count of the rain sensor. A flip equals 0.258 mm of rain. |
| ws | The measured windspeed in m/s. |
| wg | The measured gust in m/s. |
| wd | The wind direction. 0: N, 1: NNE, 2: NE, 3: ENE, 4: E, 5: ESE, 6: SE, 7: SSE, 8: S, 9: SSW, 10: SW, 11: WSW, 12: W, 13: WNW, 14: NW, 15: NNW. Direction degrees = wd * 22.5 |
| w | If the window is opened or closed. |
| h3havg | Average humidity of the last 3 hours. |
| h24havg | Average humidity of the last 24 hours. |
| h7davg | Average humidity of the last 7 days. |
| h30davg | Average humidity of the last 30 days. |
| kp1t | The key press type. |
| kp1c | The running counter of key presses. |
| kp2t | The key press type. |
| kp2c | The running counter of key presses. |
| kp3t | The key press type. |
| kp3c | The running counter of key presses. |
| kp4t | The key press type. |
| kp4c | The running counter of key presses. |
| sc | If the measurement occured because of a status |
| ap | The measured air pressure in hPa. |
| water | water presence sensor (t2 of MA10350) |

## development
based on the DataUpdateCoordinator and CoordinatorEntity classes

see [https://developers.home-assistant.io/docs/integration_fetching_data/](https://developers.home-assistant.io/docs/integration_fetching_data/)

raw data can be viewed using 
```
curl -d "{'deviceids': 'XXXXXXXXXXXX'}" -H "Content-Type: application/json" https://www.data199.com/api/pv1/device/lastmeasurement
```

