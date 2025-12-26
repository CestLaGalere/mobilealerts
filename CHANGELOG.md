# Release History

[Back](./README.md)

## v.2.2.0 (Dec 26 2025)

- **feat**: Add device TFA Dostmann KLIMA@HOME 30.3060 (based on Mobile Alerts), issue [44](https://github.com/CestLaGalere/mobilealerts/issues/44)
- **feat**: Add device TFA Dostmann Temperature/Humidity Transmitter for WEATERHUB 30.3303 (based on Mobile Alerts), issue [47](https://github.com/CestLaGalere/mobilealerts/issues/47)
- **chore**: Add button installation decription in readme
- **chore**: Show correct manufacturer on device info page, either "Mobile Alerts" or "TFA Dostmann"
- **fix**: Option Symbol (option flow) removed, threw an error 500 (internal server error), issue [47](https://github.com/CestLaGalere/mobilealerts/issues/47)

## v2.1.0 (Dec 15 2025)

- **fix**: Air pressure device MA10238 had wrong humidity key (error) [#40](https://github.com/CestLaGalere/mobilealerts/issues/40)
- **fix**: Fix unit in rain flip counter from mm to none. Count history. Needed a separate sensor. [#41](https://github.com/CestLaGalere/mobilealerts/issues/41)
- **feat**: Add sensor MA10250PRO in device list with existing sensors types [#40](https://github.com/CestLaGalere/mobilealerts/issues/40)
- **feat**: Add sensor MA10410 weather station [#45](https://github.com/CestLaGalere/mobilealerts/issues/45)
- **feat**: Add service `Dump Raw API Response` which can be called by user. The service dumps the raw json for all configured devices.
- **chore**: Adapt readme.md with better log info and describe how to count the rain sensor (with use of Utility Meters)


## v2.0.0 (Dec 3 2025)

- **feat**: Add a device via UI on page Settings -> Device & services -> Integrations -> mobile Alerts, Current YAML configuration still works in parallel, information for migration in readme
- **feat**: The entity types and device models are regognized during setup automatically or when similar sensor types user is asked which device he adds (list of potential devices).
- **feat**: Bundle all Entities of a physical device into a device on HA (issue [#35](https://github.com/CestLaGalere/mobilealerts/issues/35))
- **feat**: Added entities battery status and last seen timestamp for each device (issue [#19](https://github.com/CestLaGalere/mobilealerts/issues/19))
- **feat**: Added water sensor for MA 10350 (must be confirmed by issue owner) [#5](https://github.com/CestLaGalere/mobilealerts/issues/5)
- **feat**: Multi language support. All labes are translated in de, es, fr, pt, zh-Hans

For developers:

- **chore**: Large sensor.py file splittet in smaler files (sensor, coordinator, sensor_classes, ap)
- **chore**: Warning Log for unknown new device types with API result for better issue support
- **feat**: .devcontainer folder with short readme. HA developing is based on dev containers (VS Code remote exension WSL or SSH). More info on [HA Documentation](https://developers.home-assistant.io/docs/setup_devcontainer_environment/)
- **feat**: Unit tests (pytest) for sensors, api, config_flow
- **feat**: New Mock-API server with all Device Types MA10xxx as json string. This allows 1:1 testting in browser with HA installed in dev container. (see [Document Manual Testing Scripts.md](scripts/Manual Testing Scripts.md))

## v1.3.0 (Jul 7 2025)

- **feat**: use `async_refresh` instead of `async_config_entry_first_refresh` during setup_platform HA 2025.11 compliance #31
- **fix**: HA Core warnings
- **fix**: replace banned `async_timeout` by `asyncio.timeout`
- **fix**: logging typo, cleanup unused variable
- **fix**: clean up or deprecations, typings, warnings, formating from HA Core
- **chore**: better changelog

## v1.3.0-beta1 (Jun 14 2025)

- **feat**: use `async_refresh` instead of `async_config_entry_first_refresh` during setup_platform HA 2025.11 compliance #31
- **fix**: HA Core warnings
- **fix**: replace banned `async_timeout` by `asyncio.timeout`
- **fix**: logging typo, cleanup unused variable
- **fix**: clean up or deprecations, typings, warnings, formating from HA Core
- **chore**: better changelog

## v1.2.3 (Aug 22 2024)

- **fix**: HA 2025.5 compliance #28 #26

## v1.2.2 (Jan 11 2024)

- **fix**: casting type to float #16

## v1.2.1 (Jan 9 2024)

- **fix**: Sensor `_attr_native_value` type casting #15
- **fix**: upgrade deprecated `LENGTH_MILLIMETERS` to `UnitOfLength.MILLIMETERS` #14

## v1.2.0 (Dec 11 2023)

- **fix**: add allowed ranges for humidity and temperature #8
- **feat**: binary sensor MobileAlertsWaterSensor #5

## v1.2.0-beta1 (Jun 16 2023)

- **feat**: binary sensor MobileAlertsWaterSensor #5

## v1.1.1 (16 Jun 2023)

- MobileAlertsRainSensor SensorDeviceClass changed to PRECIPITATION

## v1.1.0 (9 Jun 2023)

- Domain change - BREAKING CHANGE, change mobilealerts in config yaml to mobile_alerts
- Temperature and Rain Sensor classes created
- can see icon of this integration in UI
- Refactoring - python types, formating, etc..
- GitHub actions - on each push code is validate if contains correct manifest.json and hacs.json
- native HA attributes and properties - no need to override lot - just write to correct properties
- docs improvement

## v1.x (18 Jan 23)

- now calls the mobile alerts api rather than scraping the web page
- Breaking The type is now the key defined in the mobile alerts api
- phoneid is optional
