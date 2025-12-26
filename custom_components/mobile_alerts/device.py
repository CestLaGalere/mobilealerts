"""Mobile Alerts device management."""

import logging
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceInfo

from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)

# Device model mapping based on mobile-alerts.eu website and API documentation
# Maps model identifiers to device specifications
# Measurement keys reference:
# - t1: Internal temperature, t2: Cable/external temperature
# - h: Humidity (standard), h1: Humidity (alternative)
# - ap: Air pressure
# - r: Rainfall, rf: Rain flip counter
# - ws: Wind speed, wg: Wind gust, wd: Wind direction
# - w: Window/door contact
# - ppm: CO2/air quality
# - kp*t: Key press type, kp*c: Key press counter
DEVICE_MODELS: Final = {
    "MA10100": {
        "name": "MA 10100",
        "display_name": "Wireless Thermometer",
        "measurement_keys": {"t1"},
        "description": "Temperature sensor",
        "manufacturer": "Mobile Alerts",
    },
    "MA10101": {
        "name": "MA 10101",
        "display_name": "Wireless Thermometer with Cable Sensor",
        "measurement_keys": {"t1", "t2"},
        "description": "Internal and external temperature",
        "manufacturer": "Mobile Alerts",
    },
    "MA10120": {
        "name": "MA 10120",
        "display_name": "Wireless Thermometer",
        "measurement_keys": {"t1"},
        "description": "Temperature sensor",
        "manufacturer": "Mobile Alerts",
    },
    "MA10200": {
        "name": "MA 10200",
        "display_name": "Wireless Thermo-Hygrometer",
        "measurement_keys": {"t1", "h"},
        "description": "Temperature and humidity",
        "manufacturer": "Mobile Alerts",
    },
    "MA10230": {
        "name": "MA 10230",
        "display_name": "Wireless Room Climate Station",
        "measurement_keys": {"t1", "h", "h3havg", "h24havg", "h7davg", "h30davg"},
        "description": "Temperature and humidity",
        "manufacturer": "Mobile Alerts",
    },
    "MA10238": {
        "name": "MA 10238",
        "display_name": "Wireless Air Pressure Monitor",
        "measurement_keys": {"t1", "h", "ap"},
        "description": "Temperature, humidity, and air pressure",
        "manufacturer": "Mobile Alerts",
    },
    "MA10241": {
        "name": "MA 10241",
        "display_name": "Wireless Thermo-Hygrometer",
        "measurement_keys": {"t1", "h"},
        "description": "Temperature and humidity",
        "manufacturer": "Mobile Alerts",
    },
    "MA10300": {
        "name": "MA 10300 / MA 10320",
        "display_name": "Wireless Thermo-Hygrometer with Cable Sensor",
        "measurement_keys": {"t1", "t2", "h"},
        "description": "Temperature (internal/cable) and humidity",
        "manufacturer": "Mobile Alerts",
    },
    "MA10350": {
        "name": "MA 10350",
        "display_name": "Wireless Thermo-Hygrometer with Water Detector",
        "measurement_keys": {
            "t1",
            "t2",
            "h",
        },  # t2 = water level (NOT cable temperature like MA10300)
        "description": "Temperature, humidity, and water detection",
        "manufacturer": "Mobile Alerts",
    },
    "MA10402": {
        "name": "MA 10402",
        "display_name": "Wireless CO2 Monitor",
        "measurement_keys": {"t1", "t2", "h", "ppm"},
        "description": "Temperature, humidity, and CO2 monitoring",
        "manufacturer": "Mobile Alerts",
    },
    "MA10410": {
        "name": "MA 10410",
        "display_name": "Weather Station",
        "measurement_keys": {"t1", "t2", "h", "h2"},
        "description": "Temperature indoor, humidity indoor, temperature outdoor, humidity outdoor",
        "manufacturer": "Mobile Alerts",
    },
    "MA10450": {
        "name": "MA 10450",
        "display_name": "Wireless Temperature Station",
        "measurement_keys": {"h1"},
        "description": "Humidity sensor",
        "manufacturer": "Mobile Alerts",
    },
    "MA10650": {
        "name": "MA 10650",
        "display_name": "Wireless Rain Gauge",
        "measurement_keys": {"t1", "r", "rf"},
        "description": "Rainfall measurement and flip counter",
        "manufacturer": "Mobile Alerts",
    },
    "MA10660": {
        "name": "MA 10660",
        "display_name": "Wireless Anemometer",
        "measurement_keys": {"ws", "wg", "wd"},
        "description": "Wind speed, gust, and direction",
        "manufacturer": "Mobile Alerts",
    },
    "MA10700": {
        "name": "MA 10700",
        "display_name": "Wireless Thermo-Hygrometer with Pool Sensor",
        "measurement_keys": {"t1", "h1", "t2"},
        "description": "Temperature, humidity, and pool temperature",
        "manufacturer": "Mobile Alerts",
    },
    "MA10800": {
        "name": "MA 10800",
        "display_name": "Wireless Contact Sensor",
        "measurement_keys": {"w"},
        "description": "Window/door contact detection",
        "manufacturer": "Mobile Alerts",
    },
    "MA10880": {
        "name": "MA 10880",
        "display_name": "Wireless Switch",
        "measurement_keys": {
            "kp1t",
            "kp1c",
            "kp2t",
            "kp2c",
            "kp3t",
            "kp3c",
            "kp4t",
            "kp4c",
        },
        "description": "4-channel wireless switch with key press monitoring",
        "manufacturer": "Mobile Alerts",
    },
    "TFA_30.3060.01:IT": {
        "name": "TFA 30.3060.01",
        "display_name": "TFA Dostmann KLIMA@HOME Thermo-Hygrometer with 3 sensors",
        "measurement_keys": {"t1", "t2", "t3", "t4", "h1", "h2", "h3", "h4"},
        "description": "Temperature, humidity 1 internal sensor and up to 3 external sensors",
        "manufacturer": "TFA Dostmann",
    },
    "TFA_30.3303.02": {
        "name": "TFA 30.3303",
        "display_name": "TFA Dostmann Thermo-Hygrometer Transmitter for WEATHERHUB",
        "measurement_keys": {"t1", "h"},
        "description": "Wireless temperature and humidity transmitter for WEATHERHUB system",
        "manufacturer": "TFA Dostmann",
    },
    # MA10870 (Voltage Monitor) - measurement keys unknown, excluded from detection
}


def find_all_matching_models(
    measurement: dict[str, Any] | None,
) -> list[tuple[str, dict[str, Any]]]:
    """Find ALL device models that match the given measurement data.

    Tries exact match first, then falls back to subset matching (with scoring).
    Used by config_flow to detect devices and handle ambiguous cases.

    Args:
        measurement: The measurement dict from API response or None

    Returns:
        List of (model_id, model_info) tuples that match.
        - Empty list if no matches found
        - Single item if one model matches
        - Multiple items if ambiguous (e.g., MA10300 vs MA10350)
    """
    if not measurement:
        return []

    # Get available measurement keys
    keys = set(measurement.keys())

    # Remove metadata keys
    keys.discard("idx")
    keys.discard("ts")
    keys.discard("c")
    keys.discard("lb")

    # Remove alert flag keys
    alert_suffixes = [
        "hi",
        "lo",
        "hise",
        "lose",
        "hiee",
        "loee",
        "his",
        "los",
        "aactive",
        "as",
        "active",
        "st",
    ]
    keys = {k for k in keys if not any(k.endswith(suffix) for suffix in alert_suffixes)}

    if not keys:
        return []

    _LOGGER.debug("Detected measurement keys (after cleanup): %s", keys)

    # Try exact match first (most accurate)
    exact_matches = []
    for model_id, model_info in DEVICE_MODELS.items():
        if keys == model_info["measurement_keys"]:
            exact_matches.append((model_id, model_info))
            _LOGGER.debug(
                "Exact match found for model %s with measurement_keys: %s",
                model_id,
                keys,
            )

    # If we have exact matches, return all of them
    if exact_matches:
        _LOGGER.debug(
            "Found %d exact match(es): %s",
            len(exact_matches),
            [model_id for model_id, _ in exact_matches],
        )
        return exact_matches

    # Try subset match (device has at least these keys)
    # Use scoring to prefer models with more matching keys
    best_score = 0
    subset_matches = []

    for model_id, model_info in DEVICE_MODELS.items():
        if model_info["measurement_keys"].issubset(keys):
            # Score = number of model keys that match
            # This prefers models with more required keys
            score = len(model_info["measurement_keys"])

            if score > best_score:
                best_score = score
                subset_matches = [(model_id, model_info)]
                _LOGGER.debug(
                    "Better subset match found for model %s (score=%d). "
                    "Model keys: %s, Actual keys: %s",
                    model_id,
                    score,
                    model_info["measurement_keys"],
                    keys,
                )
            elif score == best_score:
                # Multiple models with same score - add to list
                subset_matches.append((model_id, model_info))
                _LOGGER.debug(
                    "Equal subset match found for model %s (score=%d). "
                    "Model keys: %s, Actual keys: %s",
                    model_id,
                    score,
                    model_info["measurement_keys"],
                    keys,
                )
            else:
                _LOGGER.debug(
                    "Subset match rejected for model %s (score=%d < current_best=%d). "
                    "Model keys: %s, Actual keys: %s",
                    model_id,
                    score,
                    best_score,
                    model_info["measurement_keys"],
                    keys,
                )

    if subset_matches:
        _LOGGER.debug(
            "Found %d subset match(es) with score %d: %s",
            len(subset_matches),
            best_score,
            [model_id for model_id, _ in subset_matches],
        )
        return subset_matches

    # Unknown device
    _LOGGER.warning(
        "Could not detect Mobile Alerts device model. Measurement keys: %s. "
        "Please report this with the full log output.",
        keys,
    )
    return []


def get_sensor_type_override(model_id: str, measurement_key: str) -> str | None:
    """Get sensor type override for model-specific measurement key handling.

    Some measurement keys have different meanings across models:
    - MA10300: t2 = cable temperature (TemperatureSensor)
    - MA10350: t2 = water level (WaterSensor)

    This returns the sensor type to use, overriding MEASUREMENT_TYPE_MAP.

    Args:
        model_id: Device model ID (e.g., "MA10350")
        measurement_key: The API measurement key (e.g., "t2")

    Returns:
        Sensor type string for MEASUREMENT_TYPE_MAP lookup, or None for default
    """
    # Model-specific overrides: return the sensor type to use
    overrides = {
        ("MA10350", "t2"): "water",  # MA10350: t2 is water level, not temperature
    }

    override_key = (model_id, measurement_key)
    if override_key in overrides:
        sensor_type = overrides[override_key]
        _LOGGER.debug(
            "Model %s: measurement key '%s' uses sensor type '%s' (override)",
            model_id,
            measurement_key,
            sensor_type,
        )
        return sensor_type

    # No override - use measurement_key as sensor type (default behavior)
    return None


class MobileAlertsDevice:
    """Represents a Mobile Alerts device."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        name: str,
        phone_id: str | None = None,
        manufacturer: str | None = None,
    ) -> None:
        """Initialize device."""
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.phone_id = phone_id
        self.manufacturer = manufacturer or "Mobile Alerts"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for this device."""
        return f"{DOMAIN}_{self.device_id}"

    def get_device_info(self) -> DeviceInfo:
        """Return device info for Home Assistant device registry."""
        identifiers = {(DOMAIN, self.device_id)}

        return DeviceInfo(
            identifiers=identifiers,
            name=self.name,
            manufacturer=self.manufacturer,
            model=self.device_type,
        )


class MobileAlertsDeviceManager:
    """Manage Mobile Alerts devices in Home Assistant."""

    def __init__(self, hass: HomeAssistant, device_registry: DeviceRegistry) -> None:
        """Initialize device manager."""
        self._hass = hass
        self._device_registry = device_registry
        self._devices: dict[str, MobileAlertsDevice] = {}

    def add_device(
        self,
        device_id: str,
        device_type: str,
        name: str,
        phone_id: str | None = None,
        manufacturer: str | None = None,
    ) -> MobileAlertsDevice:
        """Add or update a device."""
        device = MobileAlertsDevice(
            device_id=device_id,
            device_type=device_type,
            name=name,
            phone_id=phone_id,
            manufacturer=manufacturer,
        )

        self._devices[device_id] = device
        _LOGGER.debug("Device added: %s (%s)", name, device_id)

        return device

    def get_device(self, device_id: str) -> MobileAlertsDevice | None:
        """Get device by ID."""
        return self._devices.get(device_id)

    def get_all_devices(self) -> list[MobileAlertsDevice]:
        """Get all registered devices."""
        return list(self._devices.values())

    def remove_device(self, device_id: str) -> None:
        """Remove a device."""
        if device_id in self._devices:
            del self._devices[device_id]
            _LOGGER.debug("Device removed: %s", device_id)
