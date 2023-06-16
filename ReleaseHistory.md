# Release History

[Back](./README.md)


version

1.1.1 (16 Jun 23)
- MobileAlertsRainSensor SensorDeviceClass changed to PRECIPITATION

1.1.0 (9 Jun 23)
@petrleocompel
- Domain change - BREAKING CHANGE, change mobilealerts in config yaml to mobile_alerts
- Temperature and Rain Sensor classes created
- can see icon of this integration in UI
- Refactoring - python types, formating, etc..
- GitHub actions - on each push code is validate if contains correct manifest.json and hacs.json
- native HA attributes and properties - no need to override lot - just write to correct properties
- docs improvement

18 Jan 23
- now calls the mobile alerts api rather than scraping the web page
- Breaking The type is now the key defined in the mobile alerts api
- phoneid is optional