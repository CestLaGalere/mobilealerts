# mobilealerts for Home Assistant

integrates home assistant to the mobilealerts sensor reading service

## Installation
To install this integration you will need to add this as a custom repository in HACS.
Open HACS page, then click integrations
Click the three dots top right, select Custom repositories

1. URL enter <https://github.com/cestlagalere/mobilealerts>
2. Catgory select Integration
3. click Add

Once installed you will then be able to install this integration from the HACS integrations page.

Restart your Home Assistant to complete the installation.

## Configuration

add elements to yaml sensor section:
sensor:
  - platform: mobilealerts
    name: [enter name]
    phone_id: 123456789012
    devices:
      - device_id: 0327312EA36A
        name: Outside Temp
        type: temperature
      - device_id: 0327312EA36A
        name: Outside Humidity
        type: humidity

type: one of temperature, humidity, rain


## development
based on the DataUpdateCoordinator and CoordinatorEntity classes

see https://developers.home-assistant.io/docs/integration_fetching_data/