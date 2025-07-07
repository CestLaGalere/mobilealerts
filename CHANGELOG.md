# Release History

[Back](./README.md)

## v1.3.0 (Jul 7 2025)

- **feat**: use `async_refresh` instead of `async_config_entry_first_refresh` during setup_platform HA 2025.11 compliance #31
- **fix**: HA Core warnings
- **fix**: replace banned `async_timeout` by `asyncio.timeout`
- **fix**: logging typo, cleanup unused variable
- **fix**: clean up or deprecations, typings, warnings, formating from HA Core
- **chore**: better changelog


## v1.3.0-beta1 (Jun 14 2025)

- **feat**: use `async_refresh` instead of `async_config_entry_first_refresh` during setup_platform HA 2025.11 compliance #31
- **fix**: HA Core warnings
- **fix**: replace banned `async_timeout` by `asyncio.timeout`
- **fix**: logging typo, cleanup unused variable
- **fix**: clean up or deprecations, typings, warnings, formating from HA Core
- **chore**: better changelog

## v1.2.3 (Aug 22 2024)

- **fix**: HA 2025.5 compliance #28 #26

## v1.2.2 (Jan 11 2024)

- **fix**: casting type to float #16

## v1.2.1 (Jan 9 2024)

- **fix**: Sensor `_attr_native_value` type casting #15
- **fix**: upgrade deprecated `LENGTH_MILLIMETERS` to `UnitOfLength.MILLIMETERS` #14

## v1.2.0 (Dec 11 2023)

- **fix**: add allowed ranges for humidity and temperature #8
- **feat**: binary sensor MobileAlertsWaterSensor #5

## v1.2.0-beta1 (Jun 16 2023)

- **feat**: binary sensor MobileAlertsWaterSensor #5

## v1.1.1 (16 Jun 2023)

- MobileAlertsRainSensor SensorDeviceClass changed to PRECIPITATION

## v1.1.0 (9 Jun 2023)

- Domain change - BREAKING CHANGE, change mobilealerts in config yaml to mobile_alerts
- Temperature and Rain Sensor classes created
- can see icon of this integration in UI
- Refactoring - python types, formating, etc..
- GitHub actions - on each push code is validate if contains correct manifest.json and hacs.json
- native HA attributes and properties - no need to override lot - just write to correct properties
- docs improvement

## v1.x (18 Jan 23)

- now calls the mobile alerts api rather than scraping the web page
- Breaking The type is now the key defined in the mobile alerts api
- phoneid is optional
