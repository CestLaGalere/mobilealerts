"""Tests for Mobile Alerts sensor entities."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_TYPE,
    PERCENTAGE,
    EntityCategory,
    UnitOfPressure,
)
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.mobile_alerts.api import MobileAlertsApi
from custom_components.mobile_alerts.const import DOMAIN
from custom_components.mobile_alerts.sensor import (
    MobileAlertsBatterySensor,
    MobileAlertsCoordinator,
    MobileAlertsHumiditySensor,
    MobileAlertsLastSeenSensor,
    MobileAlertsTemperatureSensor,
)
from custom_components.mobile_alerts.sensor_classes import (
    MobileAlertsACPowerSensor,
    MobileAlertsCO2Sensor,
    MobileAlertsPressureSensor,
    MobileAlertsRainSensor,
    MobileAlertsWindDirectionDegreesSensor,
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
    return {CONF_DEVICE_ID: "A1B2C3D4E5F6", CONF_NAME: "Test Device", CONF_TYPE: "t1"}


@pytest.fixture
def sample_device_info():
    """Create sample device info."""
    return DeviceInfo(
        identifiers={(DOMAIN, "A1B2C3D4E5F6")},
        name="Test Device",
        manufacturer="Mobile Alerts",
        model="Mobile Alerts Sensor",
        serial_number="A1B2C3D4E5F6",
    )


@pytest.mark.asyncio
async def test_temperature_sensor_initialization(
    mock_coordinator, sample_device, sample_device_info
):
    """Test temperature sensor initialization."""
    sensor = MobileAlertsTemperatureSensor(
        mock_coordinator, sample_device, sample_device_info
    )

    assert sensor._device_id == "A1B2C3D4E5F6"
    assert (
        not hasattr(sensor, "_attr_name") or sensor._attr_name is None
    )  # UNDEFINED when translation_key is set
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "temperature_t1"
    assert sensor._type == "t1"
    assert sensor._device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_unique_id == "A1B2C3D4E5F6t1"
    assert sensor._attr_device_info == sample_device_info


@pytest.mark.asyncio
async def test_humidity_sensor_initialization(
    mock_coordinator, sample_device, sample_device_info
):
    """Test humidity sensor initialization."""
    humidity_device = sample_device.copy()
    humidity_device[CONF_TYPE] = "h"

    sensor = MobileAlertsHumiditySensor(
        mock_coordinator, humidity_device, sample_device_info
    )

    assert sensor._device_id == "A1B2C3D4E5F6"
    assert not hasattr(sensor, "_attr_name") or sensor._attr_name is None
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "humidity"
    assert sensor._type == "h"
    assert sensor._device_class == SensorDeviceClass.HUMIDITY
    assert sensor._attr_native_unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_battery_sensor_initialization(
    mock_coordinator, sample_device, sample_device_info
):
    """Test battery sensor initialization."""
    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )

    assert sensor._device_id == "A1B2C3D4E5F6"
    assert not hasattr(sensor, "_attr_name") or sensor._attr_name is None
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "battery"
    assert sensor._type == "battery"
    assert sensor._device_class is None  # Generic sensor for string values
    assert sensor._attr_native_unit_of_measurement is None  # String-based, no unit
    assert sensor._attr_unique_id == "A1B2C3D4E5F6_battery"


@pytest.mark.asyncio
async def test_last_seen_sensor_initialization(
    mock_coordinator, sample_device, sample_device_info
):
    """Test last seen sensor initialization."""
    sensor = MobileAlertsLastSeenSensor(
        mock_coordinator, sample_device, sample_device_info
    )

    assert sensor._device_id == "A1B2C3D4E5F6"
    assert not hasattr(sensor, "_attr_name") or sensor._attr_name is None
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "last_seen"
    assert sensor._type == "last_seen"
    assert sensor._device_class == SensorDeviceClass.TIMESTAMP
    assert sensor._attr_unique_id == "A1B2C3D4E5F6_last_seen"


@pytest.mark.asyncio
async def test_battery_sensor_extract_reading(
    mock_coordinator, sample_device, sample_device_info
):
    """Test battery sensor data extraction."""
    # Mock API response with battery data
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": False,  # Battery OK
            "idx": 123,
        },
    }

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert sensor._attr_native_value == "OK"
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_battery_sensor_extract_reading_normalized(
    mock_coordinator, sample_device, sample_device_info
):
    """Test battery sensor data extraction with low battery."""
    # Mock API response with low battery status
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "lowbattery": True,  # Low battery
            "idx": 123,
        },
    }

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert sensor._attr_native_value == "Low"
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_battery_sensor_no_lowbattery_field(
    mock_coordinator, sample_device, sample_device_info
):
    """Test battery sensor when no lowbattery field is present."""
    # Mock API response without lowbattery field
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "idx": 123,
            # No lowbattery field
        },
    }

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    # Should default to "OK" when no lowbattery field
    assert sensor._attr_native_value == "OK"
    assert sensor._attr_available
    assert sensor._attr_icon == "mdi:battery"  # Normal battery icon


@pytest.mark.asyncio
async def test_battery_sensor_icon_logic(
    mock_coordinator, sample_device, sample_device_info
):
    """Test battery sensor icon changes based on status."""
    # Test Low battery
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {"ts": 1699000000, "t1": 23.5, "lowbattery": True, "idx": 123},
    }

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert sensor._attr_native_value == "Low"
    assert sensor._attr_icon == "mdi:battery-low"

    # Test OK battery
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {"ts": 1699000000, "t1": 23.5, "lowbattery": False, "idx": 123},
    }

    sensor.extract_reading()

    assert sensor._attr_native_value == "OK"
    assert sensor._attr_icon == "mdi:battery"


@pytest.mark.asyncio
async def test_last_seen_sensor_extract_reading(
    mock_coordinator, sample_device, sample_device_info
):
    """Test last seen sensor data extraction."""
    # Mock API response with timestamp data
    test_timestamp = 1699000000
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {
            "ts": 1699000000,
            "t1": 23.5,
            "c": test_timestamp,  # Last seen timestamp
            "idx": 123,
        },
    }

    sensor = MobileAlertsLastSeenSensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert isinstance(sensor._attr_native_value, datetime)
    assert sensor._attr_native_value == datetime.fromtimestamp(
        test_timestamp, tz=timezone.utc
    )
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_last_seen_sensor_fallback_to_ts(
    mock_coordinator, sample_device, sample_device_info
):
    """Test last seen sensor falls back to 'ts' when 'c' is absent (e.g. MA10870)."""
    test_timestamp = 1772833234
    mock_coordinator.get_reading.return_value = {
        "deviceid": "173A4E25385D",
        "measurement": {
            "ts": test_timestamp,
            "t1": 17.5,
            "t2": 0.0,
            # No 'c' field - MA10870 behaviour
        },
    }

    sensor = MobileAlertsLastSeenSensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert isinstance(sensor._attr_native_value, datetime)
    assert sensor._attr_native_value == datetime.fromtimestamp(
        test_timestamp, tz=timezone.utc
    )
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_sensor_no_data(mock_coordinator, sample_device, sample_device_info):
    """Test sensor behavior when no data is available."""
    mock_coordinator.get_reading.return_value = None

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert sensor._attr_native_value is None
    assert not sensor._attr_available


@pytest.mark.asyncio
async def test_sensor_no_measurement_data(
    mock_coordinator, sample_device, sample_device_info
):
    """Test sensor behavior when measurement data is missing."""
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        # No "measurement" key
    }

    sensor = MobileAlertsBatterySensor(
        mock_coordinator, sample_device, sample_device_info
    )
    sensor.extract_reading()

    assert sensor._attr_native_value is None
    assert not sensor._attr_available


@pytest.mark.asyncio
async def test_mobile_alerts_api_initialization():
    """Test MobileAlertsApi initialization."""
    api = MobileAlertsApi("123456")

    assert api._phone_id == "123456"
    assert len(api._device_ids) == 0

    # Register devices (directly, for unit test)
    if "ABC123" not in api._device_ids:
        api._device_ids.append("ABC123")
    if "DEF456" not in api._device_ids:
        api._device_ids.append("DEF456")

    assert len(api._device_ids) == 2
    assert "ABC123" in api._device_ids
    assert "DEF456" in api._device_ids


@pytest.mark.asyncio
async def test_temperature_sensor_value_validation(sample_device_info):
    """Test temperature sensor value validation."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {"t1": 23.5, "ts": 1699000000},
    }

    sensor = MobileAlertsTemperatureSensor(
        mock_coordinator,
        {CONF_DEVICE_ID: "A1B2C3D4E5F6", CONF_NAME: "Test Temp", CONF_TYPE: "t1"},
        sample_device_info,
    )

    sensor.extract_reading()

    # Test native_value property validation
    assert sensor.native_value == 23.5

    # Test extreme values
    sensor._attr_native_value = 150  # Too high
    assert sensor.native_value is None

    sensor._attr_native_value = -150  # Too low
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_humidity_sensor_value_validation(sample_device_info):
    """Test humidity sensor value validation."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "A1B2C3D4E5F6",
        "measurement": {"h": 65.5, "ts": 1699000000},
    }

    sensor = MobileAlertsHumiditySensor(
        mock_coordinator,
        {CONF_DEVICE_ID: "A1B2C3D4E5F6", CONF_NAME: "Test Humidity", CONF_TYPE: "h"},
        sample_device_info,
    )

    sensor.extract_reading()

    # Test native_value property validation
    assert sensor.native_value == 65.5

    # Test extreme values
    sensor._attr_native_value = 150  # Too high
    assert sensor.native_value is None

    sensor._attr_native_value = -10  # Too low
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_ac_power_sensor_initialization(mock_coordinator, sample_device_info):
    """Test AC power sensor (MA10870) initialization."""
    device = {
        CONF_DEVICE_ID: "173A4E25ABCD",
        CONF_NAME: "Voltage Monitor",
        CONF_TYPE: "ac_power",
    }

    from homeassistant.components.binary_sensor import BinarySensorDeviceClass

    sensor = MobileAlertsACPowerSensor(mock_coordinator, device, sample_device_info)

    assert sensor._device_id == "173A4E25ABCD"
    assert not hasattr(sensor, "_attr_name") or sensor._attr_name is None
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "ac_power"
    assert sensor._type == "ac_power"
    assert sensor._attr_device_class == BinarySensorDeviceClass.POWER
    assert sensor._attr_unique_id == "173A4E25ABCDac_power"


@pytest.mark.asyncio
async def test_ac_power_sensor_ac_on(sample_device_info):
    """Test AC power sensor when AC is ON (t2=0)."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "173A4E25ABCD",
        "measurement": {"t1": 15.9, "t2": 0.0, "ts": 1772004382},
    }

    device = {
        CONF_DEVICE_ID: "173A4E25ABCD",
        CONF_NAME: "Voltage Monitor",
        CONF_TYPE: "ac_power",
    }
    sensor = MobileAlertsACPowerSensor(mock_coordinator, device, sample_device_info)
    sensor.extract_reading()

    assert sensor._attr_is_on is True  # t2=0 → AC is ON (power present)
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_ac_power_sensor_ac_off(sample_device_info):
    """Test AC power sensor when AC is OFF (t2=1)."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = {
        "deviceid": "173A4E25ABCD",
        "measurement": {"t1": 65295, "t2": 1, "ts": 1772225691},
    }

    device = {
        CONF_DEVICE_ID: "173A4E25ABCD",
        CONF_NAME: "Voltage Monitor",
        CONF_TYPE: "ac_power",
    }
    sensor = MobileAlertsACPowerSensor(mock_coordinator, device, sample_device_info)
    sensor.extract_reading()

    assert sensor._attr_is_on is False  # t2=1 → AC is OFF (power absent)
    assert sensor._attr_available


@pytest.mark.asyncio
async def test_ac_power_sensor_no_data(sample_device_info):
    """Test AC power sensor behavior when no data available."""
    mock_coordinator = MagicMock()
    mock_coordinator.get_reading.return_value = None

    device = {
        CONF_DEVICE_ID: "173A4E25ABCD",
        CONF_NAME: "Voltage Monitor",
        CONF_TYPE: "ac_power",
    }
    sensor = MobileAlertsACPowerSensor(mock_coordinator, device, sample_device_info)
    sensor.extract_reading()

    assert sensor._attr_is_on is False
    assert not sensor._attr_available


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("reading", "expected_value", "expected_icon"),
    [
        ({"lowbat": True, "measurement": {"t1": 21.0}}, "Low", "mdi:battery-low"),
        ({"lowbat": False, "measurement": {"t1": 21.0}}, "OK", "mdi:battery"),
        ({"lowbattery": True, "measurement": {"t1": 21.0}}, "Low", "mdi:battery-low"),
        (
            {"measurement": {"t1": 21.0, "lb": True}},
            "Low",
            "mdi:battery-low",
        ),
        (
            {"lowbat": True},
            "Low",
            "mdi:battery-low",
        ),
    ],
)
async def test_battery_sensor_all_field_variants_and_diagnostic_category(
    sample_device_info, reading, expected_value, expected_icon
):
    """Test battery extraction from lowbat, lowbattery, measurement.lb and diagnostic category."""
    mock_coord = MagicMock()
    mock_coord.get_reading.return_value = reading
    device = {CONF_DEVICE_ID: "A1B2C3D4E5F6", CONF_NAME: "Test", CONF_TYPE: "t1"}

    sensor = MobileAlertsBatterySensor(mock_coord, device, sample_device_info)
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.entity_description.translation_key == "battery"
    assert sensor._attr_native_value == expected_value
    assert sensor._attr_icon == expected_icon
    assert sensor._attr_available is True


@pytest.mark.asyncio
async def test_last_seen_sensor_prefers_newer_lastseen_and_diagnostic_category(
    sample_device_info,
):
    """Test Last Seen uses newer of data['lastseen'] and measurement['c'] and is diagnostic."""
    mock_coord = MagicMock()
    # Keepalive scenario: top-level lastseen is newer than measurement.c
    mock_coord.get_reading.return_value = {
        "lastseen": 1763190000,
        "measurement": {"t1": 10.0, "c": 1762930000, "ts": 1762929900},
    }
    device = {CONF_DEVICE_ID: "A1B2C3D4E5F6", CONF_NAME: "Test", CONF_TYPE: "t1"}

    sensor = MobileAlertsLastSeenSensor(mock_coord, device, sample_device_info)
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_available is True
    assert sensor._attr_native_value == datetime.fromtimestamp(
        1763190000, tz=timezone.utc
    )

    # Also verify measurement.c wins when it is newer than lastseen
    mock_coord.get_reading.return_value = {
        "lastseen": 1762930000,
        "measurement": {"t1": 10.0, "c": 1763200000, "ts": 1763199900},
    }
    sensor.extract_reading()
    assert sensor._attr_native_value == datetime.fromtimestamp(
        1763200000, tz=timezone.utc
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("sentinel", [43530, 43530.0, 65295, 65295.0, 65296])
async def test_invalid_measurement_sentinels_filtered(sample_device_info, sentinel):
    """API error sentinels (43530 not connected, 65295/65296 out of range) yield None."""
    mock_coord = MagicMock()
    mock_coord.get_reading.return_value = {
        "measurement": {
            "t1": sentinel,
            "h": sentinel,
            "r": sentinel,
            "wd": sentinel,
        }
    }

    temp = MobileAlertsTemperatureSensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "t1"},
        sample_device_info,
    )
    hum = MobileAlertsHumiditySensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "h"},
        sample_device_info,
    )
    rain = MobileAlertsRainSensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "r"},
        sample_device_info,
    )
    wd_deg = MobileAlertsWindDirectionDegreesSensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "wd_degrees"},
        sample_device_info,
    )

    for entity in (temp, hum, rain, wd_deg):
        assert entity._attr_available is True
        assert entity._attr_native_value is None
        assert entity.native_value is None


@pytest.mark.asyncio
async def test_pressure_and_co2_sensors(sample_device_info):
    """Test dedicated pressure (hPa) and CO2 (ppm) sensor classes."""
    mock_coord = MagicMock()
    mock_coord.get_reading.return_value = {
        "measurement": {"ap": 1013.2, "ppm": 850}
    }

    pressure = MobileAlertsPressureSensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Weather", CONF_TYPE: "ap"},
        sample_device_info,
    )
    assert pressure.device_class == SensorDeviceClass.ATMOSPHERIC_PRESSURE
    assert pressure.native_unit_of_measurement == UnitOfPressure.HPA
    assert pressure.entity_description.translation_key == "pressure"
    assert pressure.native_value == 1013.2

    pressure._attr_native_value = 0
    assert pressure.native_value is None
    pressure._attr_native_value = 43530
    assert pressure.native_value is None

    co2 = MobileAlertsCO2Sensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Indoor", CONF_TYPE: "ppm"},
        sample_device_info,
    )
    assert co2.device_class == SensorDeviceClass.CO2
    assert co2.native_unit_of_measurement == CONCENTRATION_PARTS_PER_MILLION
    assert co2.entity_description.translation_key == "air_quality"
    assert co2.native_value == 850.0

    co2._attr_native_value = 0
    assert co2.native_value == 0.0
    co2._attr_native_value = -5
    assert co2.native_value is None
    co2._attr_native_value = 65295
    assert co2.native_value is None


@pytest.mark.asyncio
async def test_translation_keys_match_entity_descriptions(sample_device_info):
    """Subclassed multi-channel temperature/humidity sensors keep specific translation keys."""
    mock_coord = MagicMock()
    mock_coord.get_reading.return_value = {
        "measurement": {"t2": 18.4, "h3havg": 52.0}
    }

    temp_t2 = MobileAlertsTemperatureSensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "t2"},
        sample_device_info,
    )
    assert temp_t2._attr_translation_key == "temperature_t2"
    assert temp_t2.entity_description.translation_key == "temperature_t2"

    hum_avg = MobileAlertsHumiditySensor(
        mock_coord,
        {CONF_DEVICE_ID: "A1", CONF_NAME: "Test", CONF_TYPE: "h3havg"},
        sample_device_info,
    )
    assert hum_avg._attr_translation_key == "humidity_3h_avg"
    assert hum_avg.entity_description.translation_key == "humidity_3h_avg"
