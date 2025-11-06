"""Constants for Mobile Alerts integration."""

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mobile_alerts"

# Configuration keys
CONF_DEVICES = "devices"
CONF_PHONE_ID = "phone_id"
CONF_TYPE = "type"

ATTRIBUTION = "Data from MobileAlerts"

# Entity types
ENTITY_TYPE_TEMPERATURE = "temperature"
ENTITY_TYPE_CABLE_TEMPERATURE = "cable_temperature"
ENTITY_TYPE_HUMIDITY = "humidity"
ENTITY_TYPE_EXTERNAL_HUMIDITY = "external_humidity"
ENTITY_TYPE_RAIN = "rain"
ENTITY_TYPE_WIND_SPEED = "wind_speed"
ENTITY_TYPE_WIND_GUST = "wind_gust"
ENTITY_TYPE_WIND_DIRECTION = "wind_direction"
ENTITY_TYPE_PRESSURE = "pressure"
ENTITY_TYPE_AIR_QUALITY = "air_quality"
ENTITY_TYPE_WINDOW = "window"
ENTITY_TYPE_AC_POWER = "ac_power"
ENTITY_TYPE_BATTERY = "battery"
ENTITY_TYPE_LAST_SEEN = "last_seen"

# Measurement keys in API response (from API documentation)
MEASUREMENT_TEMPERATURE = "t1"  # Main temperature
MEASUREMENT_CABLE_TEMPERATURE = "t2"  # Cable/external temperature
MEASUREMENT_HUMIDITY = "h"
MEASUREMENT_EXTERNAL_HUMIDITY = "h2"
MEASUREMENT_RAIN = "r"
MEASUREMENT_RAIN_FLIP_COUNT = "rf"
MEASUREMENT_WIND_SPEED = "ws"
MEASUREMENT_WIND_GUST = "wg"
MEASUREMENT_WIND_DIRECTION = "wd"
MEASUREMENT_PRESSURE = "ap"
MEASUREMENT_AIR_QUALITY = "ppm"
MEASUREMENT_WINDOW = "w"
MEASUREMENT_AC_POWER = "t2"  # ID17: 0.0 = on, 1.0 = off
MEASUREMENT_BATTERY = "b"
MEASUREMENT_LAST_SEEN = "c"

# Scan interval in minutes
SCAN_INTERVAL_MINUTES = 10


def detect_device_type(measurement: dict[str, Any]) -> str:
    """Detect device type from measurement data.

    Based on the combination of available measurement keys,
    determine which device type this is.

    Args:
        measurement: The measurement dict from API response

    Returns:
        Device type string (e.g., "t1", "h", "ws") or empty string if unknown
    """
    if not measurement:
        return ""

    # Get available measurement keys
    keys = set(measurement.keys())
    # Remove meta keys that don't indicate device type
    keys.discard("idx")
    keys.discard("ts")
    keys.discard("c")
    keys.discard("lb")
    
    # Remove alert flag keys (end with "hi", "lo", "hise", "lose", "hiee", "loee", etc.)
    keys = {
        k
        for k in keys
        if not any(
            k.endswith(suffix)
            for suffix in [
                "hi",
                "lo",
                "hise",
                "lose",
                "hiee",
                "loee",
                "his",
                "los",
                "hise",
                "lose",
                "hiee",
                "loee",
                "aactive",
                "as",
                "active",
                "st",
            ]
        )
    }
    
    # Store cleaned keys for logging unknown devices
    original_keys = keys.copy()

    # Map measurement combinations to device types
    # Sorted by specificity (most specific first)

    # ID11: t1-t4, h1-h4 (Multi-Sensor 4x Temp, 4x Hum)
    if all(k in keys for k in ["t1", "t2", "t3", "t4", "h1", "h2", "h3", "h4"]):
        return "t1"  # Multi-sensor, use t1 as primary

    # ID15: kp1t-kp4t, kp1c-kp4c, sc (Funkschalter)
    if any(k in keys for k in ["kp1t", "kp2t", "kp3t", "kp4t"]):
        return "sc"  # Funk switch

    # ID12: t1, h, h3havg, h24havg, h7davg, h30davg (Thermo/Hygro with Averages)
    if all(k in keys for k in ["t1", "h"]) and any(
        k in keys for k in ["h3havg", "h24havg"]
    ):
        return "h"  # Hygro with averages

    # ID07: t1, t2, h, h2 (Dual Thermo/Hygro)
    if all(k in keys for k in ["t1", "t2", "h", "h2"]):
        return "h2"  # External humidity

    # ID05: t1, t2, h, ppm (Thermo/Hygro with Air Quality)
    if all(k in keys for k in ["t1", "t2", "h", "ppm"]):
        return "ppm"  # Air quality

    # ID08: r or rf (Rain Gauge) - check before other types
    if "r" in keys or "rf" in keys:
        return "r"  # Rain

    # ID0B: ws, wg, wd (Wind Sensor)
    if any(k in keys for k in ["ws", "wg", "wd"]):
        return "ws"  # Wind

    # ID10: w (Window/Door Sensor)
    if "w" in keys and len(keys) == 1:
        return "w"  # Window

    # ID18: t1, h, ap (Thermo/Hygro/Barometer)
    if all(k in keys for k in ["t1", "h", "ap"]):
        return "ap"  # Air pressure

    # ID0A: t1, a1-a4 (Thermometer with Smoke Detectors)
    if "t1" in keys and any(k in keys for k in ["a1", "a2", "a3", "a4"]):
        return "t1"  # Smoke detector

    # ID01, ID04, ID06, ID09, ID0F: t1, t2, h (Thermo with Cable Sensor)
    if all(k in keys for k in ["t1", "t2"]) and "h" in keys:
        return "t2"  # Cable temperature

    # ID01, ID0F: t1, t2 (Thermo with Cable Sensor, no humidity)
    if all(k in keys for k in ["t1", "t2"]) and "h" not in keys:
        return "t2"  # Cable temperature

    # ID17: t1, t2 (AC Control - but same as cable sensor)
    # This is ambiguous, return t2 (same as cable sensor)
    if all(k in keys for k in ["t1", "t2"]):
        return "t2"  # Cable temperature

    # ID03, ID04, ID06, ID09, ID0E, ID18: t1, h (Thermo/Hygro)
    if all(k in keys for k in ["t1", "h"]):
        return "h"  # Humidity

    # ID02, ID0A, ID20: t1 only (Thermometer)
    if keys == {"t1"}:
        return "t1"  # Temperature

    # Unknown device type - log raw data for debugging
    _LOGGER.warning(
        "Could not detect Mobile Alerts device type. Raw measurement keys: %s. "
        "This might be a new device type. Please report this with the full measurement data: %s",
        original_keys,
        measurement,
    )
    return ""


@dataclass(frozen=True)
class MobileAlertsSensorDescription:
    """Sensor description for Mobile Alerts."""

    key: str
    translation_key: str
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    native_unit_of_measurement: str | None
    measurement_key: str
    suffix: str


# Sensor definitions - like Aseko Integration
# Standard sensors supported by most devices
SENSORS: list[MobileAlertsSensorDescription] = [
    # Main temperature - supported by all temperature sensor types
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_TEMPERATURE,
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        measurement_key=MEASUREMENT_TEMPERATURE,
        suffix="",
    ),
    # Cable/external temperature sensor (ID01, ID04, ID06, ID09, ID0F)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_CABLE_TEMPERATURE,
        translation_key="cable_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        measurement_key=MEASUREMENT_CABLE_TEMPERATURE,
        suffix=" Cable",
    ),
    # Humidity - supported by multiple sensor types
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_HUMIDITY,
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        measurement_key=MEASUREMENT_HUMIDITY,
        suffix="",
    ),
    # External humidity sensor (ID07)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_EXTERNAL_HUMIDITY,
        translation_key="external_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        measurement_key=MEASUREMENT_EXTERNAL_HUMIDITY,
        suffix=" External",
    ),
    # Rain gauge (ID08)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_RAIN,
        translation_key="rain",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        measurement_key=MEASUREMENT_RAIN,
        suffix="",
    ),
    # Wind speed (ID0B)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_WIND_SPEED,
        translation_key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        measurement_key=MEASUREMENT_WIND_SPEED,
        suffix="",
    ),
    # Wind gust (ID0B)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_WIND_GUST,
        translation_key="wind_gust",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        measurement_key=MEASUREMENT_WIND_GUST,
        suffix=" Gust",
    ),
    # Air pressure (ID18)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_PRESSURE,
        translation_key="pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        measurement_key=MEASUREMENT_PRESSURE,
        suffix="",
    ),
    # Air quality (PPM) (ID05)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_AIR_QUALITY,
        translation_key="air_quality",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="ppm",
        measurement_key=MEASUREMENT_AIR_QUALITY,
        suffix="",
    ),
    # Window/door sensor status (ID10)
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_WINDOW,
        translation_key="window",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        measurement_key=MEASUREMENT_WINDOW,
        suffix="",
    ),
    # Battery level - supported by all devices
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_BATTERY,
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        measurement_key=MEASUREMENT_BATTERY,
        suffix=" Battery",
    ),
    # Last seen timestamp - supported by all devices
    MobileAlertsSensorDescription(
        key=ENTITY_TYPE_LAST_SEEN,
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=None,
        native_unit_of_measurement=None,
        measurement_key=MEASUREMENT_LAST_SEEN,
        suffix=" Last Seen",
    ),
]
