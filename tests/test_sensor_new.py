"""Tests for Mobile Alerts sensor entities - New Version."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, CONF_TYPE, PERCENTAGE

from custom_components.mobile_alerts.sensor import (
    MobileAlertsCoordinator,
    MobileAlertsTemperatureSensor,
    MobileAlertsHumiditySensor,
    MobileAlertsBatterySensor,
    MobileAlertsLastSeenSensor,
    MobileAlertsData,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator for testing."""
    mock_coord = MagicMock(spec=MobileAlertsCoordinator)
    mock_coord.get_reading = MagicMock()
    return mock_coord


@pytest.fixture
def sample_device():
    """Create a sample device configuration."""
    return {
        CONF_DEVICE_ID: "A1B2C3D4E5F6",
        CONF_NAME: "Test Device",
        CONF_TYPE: "t1"
    }


@pytest.mark.asyncio
async def test_temperature_sensor_initialization(mock_coordinator, sample_device):
    """Test temperature sensor initialization."""
    sensor = MobileAlertsTemperatureSensor(mock_coordinator, sample_device)
    
    assert sensor._device_id == "A1B2C3D4E5F6"
    assert sensor._attr_name == "Test Device"
    assert sensor._type == "t1"
    assert sensor._device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_unique_id == "A1B2C3D4E5F6t1"


@pytest.mark.asyncio
async def test_humidity_sensor_initialization(mock_coordinator, sample_device):
    """Test humidity sensor initialization."""
    humidity_device = sample_device.copy()
    humidity_device[CONF_TYPE] = "h"
    
    sensor = MobileAlertsHumiditySensor(mock_coordinator, humidity_device)
    
    assert sensor._device_id == "A1B2C3D4E5F6"
    assert sensor._attr_name == "Test Device"
    assert sensor._type == "h"
    assert sensor._device_class == SensorDeviceClass.HUMIDITY
    assert sensor._attr_native_unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_battery_sensor_initialization(mock_coordinator, sample_device):
    """Test battery sensor initialization."""
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    
    assert sensor._device_id == "A1B2C3D4E5F6"
    assert sensor._attr_name == "Test Device Battery"
    assert sensor._type == "battery"
    assert sensor._device_class is None  # Generic sensor for string values
    assert sensor._attr_native_unit_of_measurement is None  # String-based, no unit
    assert sensor._attr_unique_id == "A1B2C3D4E5F6_battery"


@pytest.mark.asyncio
async def test_last_seen_sensor_initialization(mock_coordinator, sample_device):
    """Test last seen sensor initialization."""
    sensor = MobileAlertsLastSeenSensor(mock_coordinator, sample_device)
    
    assert sensor._device_id == "A1B2C3D4E5F6"
    assert sensor._attr_name == "Test Device Last Seen"
    assert sensor._type == "last_seen"
    assert sensor._device_class == SensorDeviceClass.TIMESTAMP
    assert sensor._attr_unique_id == "A1B2C3D4E5F6_last_seen"


@pytest.mark.asyncio
async def test_battery_sensor_extract_reading(mock_coordinator, sample_device):
    """Test battery sensor data extraction."""
    # Mock API response with battery data
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": False,  # Battery OK
            "idx": 123
        }
    }
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert sensor._attr_native_value == "OK"
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_battery_sensor_extract_reading_normalized(mock_coordinator, sample_device):
    """Test battery sensor data extraction with low battery."""
    # Mock API response with low battery status
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": True,  # Low battery
            "idx": 123
        }
    }
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert sensor._attr_native_value == "Low"
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_battery_sensor_no_lowbattery_field(mock_coordinator, sample_device):
    """Test battery sensor when no lowbattery field is present."""
    # Mock API response without lowbattery field
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "idx": 123
            # No lowbattery field
        }
    }
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    # Should default to "OK" when no lowbattery field
    assert sensor._attr_native_value == "OK"
    assert sensor._attr_available
    assert sensor._attr_icon == "mdi:battery"  # Normal battery icon


@pytest.mark.asyncio
async def test_battery_sensor_icon_logic(mock_coordinator, sample_device):
    """Test battery sensor icon changes based on status."""
    # Test Low battery
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": True,
            "idx": 123
        }
    }
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert sensor._attr_native_value == "Low"
    assert sensor._attr_icon == "mdi:battery-low"
    
    # Test OK battery
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": False,
            "idx": 123
        }
    }
    
    sensor.extract_reading()
    
    assert sensor._attr_native_value == "OK"
    assert sensor._attr_icon == "mdi:battery"


@pytest.mark.asyncio
async def test_last_seen_sensor_extract_reading(mock_coordinator, sample_device):
    """Test last seen sensor data extraction."""
    # Mock API response with timestamp data
    test_timestamp = 1699000000
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "c": test_timestamp,  # Last seen timestamp
            "idx": 123
        }
    }
    
    sensor = MobileAlertsLastSeenSensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert isinstance(sensor._attr_native_value, datetime)
    assert sensor._attr_native_value == datetime.fromtimestamp(test_timestamp, tz=timezone.utc)
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_sensor_no_data(mock_coordinator, sample_device):
    """Test sensor behavior when no data is available."""
    mock_coordinator.get_reading.return_value = None
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert sensor._attr_native_value is None
    assert not sensor._attr_available


@pytest.mark.asyncio
async def test_sensor_no_measurement_data(mock_coordinator, sample_device):
    """Test sensor behavior when measurement data is missing."""
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        # No "measurement" key
    }
    
    sensor = MobileAlertsBatterySensor(mock_coordinator, sample_device)
    sensor.extract_reading()
    
    assert sensor._attr_native_value is None
    assert not sensor._attr_available


@pytest.mark.asyncio
async def test_mobile_alerts_data_initialization():
    """Test MobileAlertsData initialization."""
    devices = [
        {"device_id": "ABC123", "name": "Device 1", "type": "t1"},
        {"device_id": "DEF456", "name": "Device 2", "type": "h"},
    ]
    
    data = MobileAlertsData("123456", devices)
    
    assert data._phone_id == "123456"
    assert len(data._device_ids) == 2
    assert "ABC123" in data._device_ids
    assert "DEF456" in data._device_ids


@pytest.mark.asyncio
async def test_temperature_sensor_value_validation():
    """Test temperature sensor value validation."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "t1": 23.5,
            "ts": 1699000000
        }
    }
    
    sensor = MobileAlertsTemperatureSensor(mock_coordinator, {
        CONF_DEVICE_ID: "A1B2C3D4E5F6",
        CONF_NAME: "Test Temp",
        CONF_TYPE: "t1"
    })
    
    sensor.extract_reading()
    
    # Test native_value property validation
    assert sensor.native_value == 23.5
    
    # Test extreme values
    sensor._attr_native_value = 150  # Too high
    assert sensor.native_value is None
    
    sensor._attr_native_value = -150  # Too low
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_humidity_sensor_value_validation():
    """Test humidity sensor value validation."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "h": 65.5,
            "ts": 1699000000
        }
    }
    
    sensor = MobileAlertsHumiditySensor(mock_coordinator, {
        CONF_DEVICE_ID: "A1B2C3D4E5F6",
        CONF_NAME: "Test Humidity",
        CONF_TYPE: "h"
    })
    
    sensor.extract_reading()
    
    # Test native_value property validation
    assert sensor.native_value == 65.5
    
    # Test extreme values
    sensor._attr_native_value = 150  # Too high
    assert sensor.native_value is None
    
    sensor._attr_native_value = -10  # Too low
    assert sensor.native_value is None