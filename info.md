# MobileAlerts sensor data

## Installation

To install this integration you will need to add this as a custom repository in HACS.
Open HACS page, then click integrations
Click the three dots top right, select Custom repositories
URL enter <https://github.com/cestlagalere/mobilealerts>
Catgory select Integration
click Add

Once installed you will then be able to install this integration from the HACS integrations page.

Restart your Home Assistant to complete the installation.

## Configuration

add elements to yaml sensor section:
weather:
  \- platform: mobilealerts
    name: [enter name]
    phone_id: [12 digit phone id - obtain from teh settings page of the MobileLaerts app]
    device_id:
      \- [12 digit sensor ids]
      \- [sensorid2]
      \- etc

sensor:
  \- platform: mobilealerts
    name: temperature_min_last_24
    device_id: [12 digit id]
    device_class: temperature
    method: minimum
    duration: 24

device_class: one of temperature, rain
method: one of minimum, maximum, difference
duration: number of hours

e.g. for rainfall, use
  \- platform: mobilealerts
    name: rain_last_24
    device_id: [rain gauge deviceid]
    device_class: rain
    method: difference
    duration: 24

also
  \- platform: mobilealerts
    name: [name]
    devices:
      \- rain
      \- temperature
      \- gust
      \- humidity
      \- wind direction
      \- windspeed
    weather: weather.[weathername]

  \- platform: mobilealerts
    name: [location]
    devices:
      \- pressure
    weather: weather.openweathermap
