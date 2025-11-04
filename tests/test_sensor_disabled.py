"""Tests for Mobile Alerts sensor entities."""

import pytest
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant

from custom_components.mobile_alerts.const import (
    ENTITY_TYPE_AIR_QUALITY,
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_CABLE_TEMPERATURE,
    ENTITY_TYPE_EXTERNAL_HUMIDITY,
    ENTITY_TYPE_HUMIDITY,
    ENTITY_TYPE_LAST_SEEN,
    ENTITY_TYPE_PRESSURE,
    ENTITY_TYPE_RAIN,
    ENTITY_TYPE_TEMPERATURE,
    ENTITY_TYPE_WINDOW,
    ENTITY_TYPE_WIND_GUST,
    ENTITY_TYPE_WIND_SPEED,
    SENSORS,
)
from custom_components.mobile_alerts.sensor import (
    MobileAlertsCoordinator,
    # MobileAlertsSensorEntity,  # TEMPORARILY DISABLED - using old sensor classes
)


@pytest.mark.asyncio
async def test_sensors_list_exists():
    """Test that SENSORS list is properly defined with all sensor types."""
    # Should have 12 sensor types now: temp, cable_temp, humidity, external_humidity,
    # rain, wind_speed, wind_gust, pressure, air_quality, window, battery, last_seen
    assert len(SENSORS) == 12
    assert SENSORS[0].key == ENTITY_TYPE_TEMPERATURE
    assert SENSORS[1].key == ENTITY_TYPE_CABLE_TEMPERATURE
    assert SENSORS[2].key == ENTITY_TYPE_HUMIDITY
    assert SENSORS[3].key == ENTITY_TYPE_EXTERNAL_HUMIDITY
    assert SENSORS[4].key == ENTITY_TYPE_RAIN
    assert SENSORS[5].key == ENTITY_TYPE_WIND_SPEED
    assert SENSORS[6].key == ENTITY_TYPE_WIND_GUST
    assert SENSORS[7].key == ENTITY_TYPE_PRESSURE
    assert SENSORS[8].key == ENTITY_TYPE_AIR_QUALITY
    assert SENSORS[9].key == ENTITY_TYPE_WINDOW
    assert SENSORS[10].key == ENTITY_TYPE_BATTERY
    assert SENSORS[11].key == ENTITY_TYPE_LAST_SEEN


@pytest.mark.asyncio
async def test_sensor_description_temperature():
    """Test temperature sensor description."""
    temp_sensor = SENSORS[0]
    assert temp_sensor.key == ENTITY_TYPE_TEMPERATURE
    assert temp_sensor.translation_key == "temperature"
    assert temp_sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert temp_sensor.state_class == SensorStateClass.MEASUREMENT
    assert temp_sensor.measurement_key == "t1"
    assert temp_sensor.suffix == ""


@pytest.mark.asyncio
async def test_sensor_description_cable_temperature():
    """Test cable temperature sensor description."""
    cable_temp_sensor = SENSORS[1]
    assert cable_temp_sensor.key == ENTITY_TYPE_CABLE_TEMPERATURE
    assert cable_temp_sensor.translation_key == "cable_temperature"
    assert cable_temp_sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert cable_temp_sensor.measurement_key == "t2"
    assert cable_temp_sensor.suffix == " Cable"


@pytest.mark.asyncio
async def test_sensor_description_humidity():
    """Test humidity sensor description."""
    humidity_sensor = SENSORS[2]
    assert humidity_sensor.key == ENTITY_TYPE_HUMIDITY
    assert humidity_sensor.translation_key == "humidity"
    assert humidity_sensor.device_class == SensorDeviceClass.HUMIDITY
    assert humidity_sensor.state_class == SensorStateClass.MEASUREMENT
    assert humidity_sensor.measurement_key == "h"


@pytest.mark.asyncio
async def test_sensor_description_external_humidity():
    """Test external humidity sensor description."""
    ext_humidity_sensor = SENSORS[3]
    assert ext_humidity_sensor.key == ENTITY_TYPE_EXTERNAL_HUMIDITY
    assert ext_humidity_sensor.translation_key == "external_humidity"
    assert ext_humidity_sensor.device_class == SensorDeviceClass.HUMIDITY
    assert ext_humidity_sensor.measurement_key == "h2"
    assert ext_humidity_sensor.suffix == " External"


@pytest.mark.asyncio
async def test_sensor_description_rain():
    """Test rain sensor description."""
    rain_sensor = SENSORS[4]
    assert rain_sensor.key == ENTITY_TYPE_RAIN
    assert rain_sensor.translation_key == "rain"
    assert rain_sensor.device_class == SensorDeviceClass.PRECIPITATION
    assert rain_sensor.measurement_key == "r"


@pytest.mark.asyncio
async def test_sensor_description_wind_speed():
    """Test wind speed sensor description."""
    wind_speed_sensor = SENSORS[5]
    assert wind_speed_sensor.key == ENTITY_TYPE_WIND_SPEED
    assert wind_speed_sensor.translation_key == "wind_speed"
    assert wind_speed_sensor.device_class == SensorDeviceClass.WIND_SPEED
    assert wind_speed_sensor.measurement_key == "ws"


@pytest.mark.asyncio
async def test_sensor_description_wind_gust():
    """Test wind gust sensor description."""
    wind_gust_sensor = SENSORS[6]
    assert wind_gust_sensor.key == ENTITY_TYPE_WIND_GUST
    assert wind_gust_sensor.translation_key == "wind_gust"
    assert wind_gust_sensor.measurement_key == "wg"
    assert wind_gust_sensor.suffix == " Gust"


@pytest.mark.asyncio
async def test_sensor_description_pressure():
    """Test pressure sensor description."""
    pressure_sensor = SENSORS[7]
    assert pressure_sensor.key == ENTITY_TYPE_PRESSURE
    assert pressure_sensor.translation_key == "pressure"
    assert pressure_sensor.device_class == SensorDeviceClass.ATMOSPHERIC_PRESSURE
    assert pressure_sensor.measurement_key == "ap"


@pytest.mark.asyncio
async def test_sensor_description_air_quality():
    """Test air quality sensor description."""
    air_quality_sensor = SENSORS[8]
    assert air_quality_sensor.key == ENTITY_TYPE_AIR_QUALITY
    assert air_quality_sensor.translation_key == "air_quality"
    assert air_quality_sensor.measurement_key == "ppm"


@pytest.mark.asyncio
async def test_sensor_description_window():
    """Test window sensor description."""
    window_sensor = SENSORS[9]
    assert window_sensor.key == ENTITY_TYPE_WINDOW
    assert window_sensor.translation_key == "window"
    assert window_sensor.measurement_key == "w"


@pytest.mark.asyncio
async def test_sensor_description_battery():
    """Test battery sensor description."""
    battery_sensor = SENSORS[10]
    assert battery_sensor.key == ENTITY_TYPE_BATTERY
    assert battery_sensor.translation_key == "battery"
    assert battery_sensor.device_class == SensorDeviceClass.BATTERY
    assert battery_sensor.measurement_key == "b"
    assert battery_sensor.suffix == " Battery"


@pytest.mark.asyncio
async def test_sensor_description_last_seen():
    """Test last seen sensor description."""
    last_seen_sensor = SENSORS[11]
    assert last_seen_sensor.key == ENTITY_TYPE_LAST_SEEN
    assert last_seen_sensor.translation_key == "last_seen"
    assert last_seen_sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert last_seen_sensor.measurement_key == "c"
    assert last_seen_sensor.suffix == " Last Seen"


@pytest.mark.asyncio
async def test_coordinator_initialization(hass: HomeAssistant):
    """Test coordinator initialization."""
    mock_api = MagicMock()
    coordinator = MobileAlertsCoordinator(hass, mock_api)

    assert coordinator._api is mock_api
    assert coordinator.hass is hass


@pytest.mark.asyncio
async def test_sensor_entity_initialization(hass: HomeAssistant, fake_device_ids):
    """Test sensor entity initialization."""
    mock_coordinator = MagicMock()
    mock_coordinator.hass = hass

    sensor_desc = SENSORS[0]  # Temperature sensor

    entity = MobileAlertsSensorEntity(
        coordinator=mock_coordinator,
        device_id=fake_device_ids[0],
        device_name="Test Device",
        device_type="t1",
        description=sensor_desc,
    )

    assert entity._device_id == fake_device_ids[0]
    assert entity._device_type == "t1"
    assert entity._attr_name == "Test Device"
    assert entity._attr_device_class == SensorDeviceClass.TEMPERATURE


@pytest.mark.asyncio
async def test_sensor_entity_name_with_suffix(hass: HomeAssistant, fake_device_ids):
    """Test sensor entity name generation with suffix."""
    mock_coordinator = MagicMock()
    mock_coordinator.hass = hass

    battery_desc = SENSORS[10]  # Battery sensor

    entity = MobileAlertsSensorEntity(
        coordinator=mock_coordinator,
        device_id=fake_device_ids[0],
        device_name="Wohnzimmer",
        device_type="t1",
        description=battery_desc,
    )

    assert entity._attr_name == "Wohnzimmer Battery"


@pytest.mark.asyncio
async def test_sensor_entity_last_seen_name(hass: HomeAssistant, fake_device_ids):
    """Test last seen sensor entity name."""
    mock_coordinator = MagicMock()
    mock_coordinator.hass = hass

    last_seen_desc = SENSORS[11]  # Last seen sensor

    entity = MobileAlertsSensorEntity(
        coordinator=mock_coordinator,
        device_id=fake_device_ids[0],
        device_name="Kinderzimmer",
        device_type="h",
        description=last_seen_desc,
    )

    assert entity._attr_name == "Kinderzimmer Last Seen"


@pytest.mark.asyncio
async def test_sensor_entity_unique_id(hass: HomeAssistant, fake_device_ids):
    """Test sensor entity unique ID generation."""
    mock_coordinator = MagicMock()
    mock_coordinator.hass = hass

    sensor_desc = SENSORS[0]  # Temperature

    entity = MobileAlertsSensorEntity(
        coordinator=mock_coordinator,
        device_id=fake_device_ids[0],
        device_name="Test",
        device_type="t1",
        description=sensor_desc,
    )

    expected_unique_id = f"{fake_device_ids[0]}_{ENTITY_TYPE_TEMPERATURE}"
    assert entity._attr_unique_id == expected_unique_id
