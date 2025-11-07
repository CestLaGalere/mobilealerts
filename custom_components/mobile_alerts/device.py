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
# - h1: Humidity
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
    },
    "MA10101": {
        "name": "MA 10101",
        "display_name": "Wireless Thermometer with Cable Sensor",
        "measurement_keys": {"t1", "t2"},
        "description": "Internal and external temperature",
    },
    "MA10120": {
        "name": "MA 10120",
        "display_name": "Wireless Thermometer",
        "measurement_keys": {"t1"},
        "description": "Temperature sensor",
    },
    "MA10200": {
        "name": "MA 10200",
        "display_name": "Wireless Thermo-Hygrometer",
        "measurement_keys": {"t1", "h1"},
        "description": "Temperature and humidity",
    },
    "MA10230": {
        "name": "MA 10230",
        "display_name": "Wireless Room Climate Station",
        "measurement_keys": {"t1", "h"},
        "description": "Temperature and humidity",
    },
    "MA10238": {
        "name": "MA 10238",
        "display_name": "Wireless Air Pressure Monitor",
        "measurement_keys": {"t1", "h1", "ap"},
        "description": "Temperature, humidity, and air pressure",
    },
    "MA10241": {
        "name": "MA 10241",
        "display_name": "Wireless Thermo-Hygrometer",
        "measurement_keys": {"t1", "h1"},
        "description": "Temperature and humidity",
    },
    "MA10300": {
        "name": "MA 10300 / MA 10320",
        "display_name": "Wireless Thermo-Hygrometer with Cable Sensor",
        "measurement_keys": {"t1", "t2", "h1"},
        "description": "Temperature (internal/cable) and humidity",
    },
    "MA10350": {
        "name": "MA 10350",
        "display_name": "Wireless Thermo-Hygrometer with Water Detector",
        "measurement_keys": {"t1", "h1", "t2"},
        "description": "Temperature, humidity, and water detection (t2 indicates water presence)",
    },
    "MA10450": {
        "name": "MA 10450",
        "display_name": "Wireless Temperature Station",
        "measurement_keys": {"h1"},
        "description": "Humidity sensor",
    },
    "MA10650": {
        "name": "MA 10650",
        "display_name": "Wireless Rain Gauge",
        "measurement_keys": {"r", "rf"},
        "description": "Rainfall measurement and flip counter",
    },
    "MA10660": {
        "name": "MA 10660",
        "display_name": "Wireless Anemometer",
        "measurement_keys": {"ws", "wg", "wd"},
        "description": "Wind speed, gust, and direction",
    },
    "MA10700": {
        "name": "MA 10700",
        "display_name": "Wireless Thermo-Hygrometer with Pool Sensor",
        "measurement_keys": {"t1", "h1", "t2"},
        "description": "Temperature, humidity, and pool temperature",
    },
    "MA10800": {
        "name": "MA 10800",
        "display_name": "Wireless Contact Sensor",
        "measurement_keys": {"w"},
        "description": "Window/door contact detection",
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
    },
    # MA10870 (Voltage Monitor) - measurement keys unknown, excluded from detection
}


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
        "This might be a new device type. Please report this with the full log output.",
        original_keys,
    )
    return ""


def detect_device_model(
    measurement: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]] | None:
    """Detect device model from measurement data.

    Args:
        measurement: The measurement dict from API response or None

    Returns:
        Tuple of (model_id, model_info) or None if unknown
        Example: ("MA10300", {"api_id": "ID06", "name": "MA 10300", ...})
    """
    if not measurement:
        return None

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
        return None

    _LOGGER.debug("Detected measurement keys (after cleanup): %s", keys)

    # Try exact match first (most accurate)
    for model_id, model_info in DEVICE_MODELS.items():
        if keys == model_info["measurement_keys"]:
            _LOGGER.debug(
                "Exact match found for model %s with measurement_keys: %s",
                model_id,
                keys,
            )
            return (model_id, model_info)

    # Try subset match (device has at least these keys)
    # Use scoring to prefer models with more matching keys
    best_match = None
    best_score = 0

    for model_id, model_info in DEVICE_MODELS.items():
        if model_info["measurement_keys"].issubset(keys):
            # Score = number of model keys that match
            # This prefers models with more required keys
            score = len(model_info["measurement_keys"])

            if score > best_score:
                best_score = score
                best_match = (model_id, model_info)
                _LOGGER.debug(
                    "Better subset match found for model %s (score=%d). "
                    "Model keys: %s, Actual keys: %s",
                    model_id,
                    score,
                    model_info["measurement_keys"],
                    keys,
                )
            else:
                _LOGGER.debug(
                    "Subset match rejected for model %s (score=%d <= current_best=%d). "
                    "Model keys: %s, Actual keys: %s",
                    model_id,
                    score,
                    best_score,
                    model_info["measurement_keys"],
                    keys,
                )

    if best_match:
        return best_match

    # Unknown device
    _LOGGER.warning(
        "Could not detect Mobile Alerts device model. Measurement keys: %s. "
        "Please report this with the full log output.",
        keys,
    )
    return None


class MobileAlertsDevice:
    """Represents a Mobile Alerts device."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        name: str,
        phone_id: str | None = None,
    ) -> None:
        """Initialize device."""
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.phone_id = phone_id

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
            manufacturer="Mobile Alerts",
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
    ) -> MobileAlertsDevice:
        """Add or update a device."""
        device = MobileAlertsDevice(
            device_id=device_id,
            device_type=device_type,
            name=name,
            phone_id=phone_id,
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
