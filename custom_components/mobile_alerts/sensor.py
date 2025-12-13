"""Support for the Mobile Alerts service."""

from datetime import timedelta
import logging
from typing import Final

import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, CONF_TYPE
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import MobileAlertsApi
from .const import (
    CONF_DEVICES,
    CONF_PHONE_ID,
    CONF_MODEL_ID,
    DOMAIN,
    SCAN_INTERVAL_MINUTES,
)
from .coordinator import MobileAlertsCoordinator
from .device import DEVICE_MODELS, get_sensor_type_override
from .sensor_classes import (
    MobileAlertsBatterySensor,
    MobileAlertsContactSensor,
    MobileAlertsHumiditySensor,
    MobileAlertsLastSeenSensor,
    MobileAlertsRainFlowSensor,
    MobileAlertsRainSensor,
    MobileAlertsSensor,
    MobileAlertsTemperatureSensor,
    MobileAlertsWaterSensor,
    MobileAlertsWindDirectionDegreesSensor,
    MobileAlertsWindDirectionSensor,
    MobileAlertsWindSpeedSensor,
    MobileAlertsWindGustSensor,
)

_LOGGER: Final = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TYPE): cv.string,
    }
)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PHONE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
    },
    extra=vol.ALLOW_EXTRA,
)

# Mapping of device types to sensor classes
# Shared between async_setup_platform and async_setup_entry to ensure consistency
MEASUREMENT_TYPE_MAP = {
    "t1": MobileAlertsTemperatureSensor,
    "t2": MobileAlertsTemperatureSensor,
    "t3": MobileAlertsTemperatureSensor,
    "t4": MobileAlertsTemperatureSensor,
    "h": MobileAlertsHumiditySensor,
    "h1": MobileAlertsHumiditySensor,
    "h2": MobileAlertsHumiditySensor,
    "h3": MobileAlertsHumiditySensor,
    "h4": MobileAlertsHumiditySensor,
    "r": MobileAlertsRainSensor,
    "rf": MobileAlertsRainFlowSensor,
    "ws": MobileAlertsWindSpeedSensor,
    "wg": MobileAlertsWindGustSensor,
    "wd": MobileAlertsWindDirectionSensor,
    "wd_degrees": MobileAlertsWindDirectionDegreesSensor,
    "w": MobileAlertsContactSensor,  # Window/door contact sensor (Boolean True/False)
    "water": MobileAlertsWaterSensor,  # Water sensor (MA10350)
    # Generic sensor class for unmapped types (will use default parent class behavior)
    # This includes key press sensors from MA 10880 Wireless Switch
    "ap": MobileAlertsSensor,  # Air Pressure
    "ppm": MobileAlertsSensor,  # Air Quality
    "kp1t": MobileAlertsSensor,  # Key Press 1 Type
    "kp1c": MobileAlertsSensor,  # Key Press 1 Counter
    "kp2t": MobileAlertsSensor,  # Key Press 2 Type
    "kp2c": MobileAlertsSensor,  # Key Press 2 Counter
    "kp3t": MobileAlertsSensor,  # Key Press 3 Type
    "kp3c": MobileAlertsSensor,  # Key Press 3 Counter
    "kp4t": MobileAlertsSensor,  # Key Press 4 Type
    "kp4c": MobileAlertsSensor,  # Key Press 4 Counter
}


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup from YAML configuration."""
    _LOGGER.debug("async_setup_platform called for Mobile Alerts YAML setup")

    phone_id = config.get(CONF_PHONE_ID, "")

    # Treat empty phone_id same as "ui_devices" (UI-configured devices)
    if not phone_id:
        phone_id = "ui_devices"

    devices_config = config.get(CONF_DEVICES, [])

    # Check for duplicate device IDs in config entries
    duplicate_device_ids = set()
    if DOMAIN in hass.data and "entries" in hass.data[DOMAIN]:
        # Collect all device_ids from config entries
        for entry in hass.data[DOMAIN]["entries"].values():
            entry_device_id = entry.data.get(CONF_DEVICE_ID)
            if entry_device_id:
                duplicate_device_ids.add(entry_device_id)

    # Filter out devices that exist in config entries and warn about them
    warned_devices = set()
    filtered_devices = []
    for device in devices_config:
        device_id = device[CONF_DEVICE_ID]
        if device_id in duplicate_device_ids and device_id not in warned_devices:
            device_name = device[CONF_NAME]
            _LOGGER.warning(
                "Mobile Alerts device '%s' (%s) is configured in both YAML (configuration.yaml) "
                "and as a config entry (via the UI). "
                "To avoid this warning, please remove the device from configuration.yaml. "
                "The UI configuration will take precedence. "
                "If you are migrating from YAML to UI configuration, you can safely delete the YAML entries.",
                device_name,
                device_id,
            )
            warned_devices.add(device_id)
            # Skip adding this device from YAML to prevent duplicate entity errors
        else:
            # Only add devices that are NOT in config entries
            filtered_devices.append(device)

    devices_config = filtered_devices

    _LOGGER.info(
        "Setting up Mobile Alerts sensors from YAML: phone_id=%s, %d device(s)",
        phone_id if phone_id else "(empty)",
        len(devices_config),
    )

    if not devices_config:
        _LOGGER.warning("No devices configured in YAML")
        return

    # Create API instance
    api = MobileAlertsApi(phone_id)

    # Register all devices with API and build device info mapping
    device_info_map = {}  # Maps device_id to device info

    for device in devices_config:
        device_id = device[CONF_DEVICE_ID]
        # Only add to list, don't fetch yet - we'll fetch after coordinator is ready
        if device_id not in api._device_ids:
            api._device_ids.append(device_id)
            _LOGGER.debug("Device %s added to API", device_id)

        # Create device info for each unique device_id (only once per device)
        if device_id not in device_info_map:
            device_name = device[CONF_NAME]
            device_type = device[CONF_TYPE]

            device_info_map[device_id] = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=device_name,
                manufacturer="Mobile Alerts",
                model=f"Manual Config - {device_type}",  # Shows measurement type for YAML config
                serial_number=device_id,
            )
            _LOGGER.debug(
                "Created device info for device_id=%s, name=%s, type=%s",
                device_id,
                device_name,
                device_type,
            )

    # Create or reuse shared coordinator per phone_id
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "coordinators" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["coordinators"] = {}

    if phone_id not in hass.data[DOMAIN]["coordinators"]:
        coordinator = MobileAlertsCoordinator(hass, api)
        hass.data[DOMAIN]["coordinators"][phone_id] = coordinator
        await coordinator.async_refresh()
        _LOGGER.debug(
            "Created new coordinator for phone_id=%s",
            phone_id if phone_id else "(empty)",
        )
    else:
        coordinator = hass.data[DOMAIN]["coordinators"][phone_id]
        _LOGGER.debug(
            "Reusing existing coordinator for phone_id=%s",
            phone_id if phone_id else "(empty)",
        )

    sensors: list[SensorEntity | BinarySensorEntity] = []
    processed_device_ids = set()

    for device in devices_config:
        device_type = device[CONF_TYPE]
        device_id = device[CONF_DEVICE_ID]

        # Create the main sensor using MEASUREMENT_TYPE_MAP
        if device_type in MEASUREMENT_TYPE_MAP:
            sensor_class = MEASUREMENT_TYPE_MAP[device_type]
            sensors.append(
                sensor_class(coordinator, device, device_info_map[device_id])
            )

        # Special case: Wind direction has two sensors (text + degrees)
        if device_type == "wd":
            device_dict = device.copy()
            device_dict[CONF_TYPE] = "wd_degrees"
            sensors.append(
                MobileAlertsWindDirectionDegreesSensor(
                    coordinator, device_dict, device_info_map[device_id]
                )
            )

        # Add Battery and Last Seen sensors only once per unique device_id
        if device_id not in processed_device_ids:
            sensors.append(
                MobileAlertsBatterySensor(
                    coordinator, device, device_info_map[device_id]
                )
            )
            sensors.append(
                MobileAlertsLastSeenSensor(
                    coordinator, device, device_info_map[device_id]
                )
            )
            processed_device_ids.add(device_id)

    add_entities(sensors)
    _LOGGER.info(
        "Added %d sensor entities from %d config entries (%d unique devices)",
        len(sensors),
        len(devices_config),
        len(processed_device_ids),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mobile Alerts sensors from a config entry."""
    _LOGGER.debug(
        "async_setup_entry called for Mobile Alerts config entry %s",
        config_entry.entry_id,
    )

    entry_data = config_entry.data
    phone_id = entry_data.get(CONF_PHONE_ID, "")

    # Treat empty phone_id same as "ui_devices" (UI-configured devices)
    if not phone_id:
        phone_id = "ui_devices"

    # Check if this is a device-based entry
    device_id = entry_data.get(CONF_DEVICE_ID)

    _LOGGER.debug("async_setup_entry: phone_id=%s, device_id=%s", phone_id, device_id)

    if device_id:
        # Single device entry (from config_flow)
        device_name = entry_data.get(CONF_NAME, f"Device {device_id}")
        model_id = entry_data.get(
            CONF_MODEL_ID, ""
        )  # Device model ID (e.g., "MA10300")
        device_type = entry_data.get(
            CONF_TYPE, ""
        )  # Could be model_id or measurement_key (for backward compatibility)

        # Backward compatibility: If no CONF_MODEL_ID, check if CONF_TYPE is a model_id
        if not model_id and device_type:
            if device_type in DEVICE_MODELS:
                model_id = device_type
                _LOGGER.debug(
                    "No CONF_MODEL_ID found, using CONF_TYPE as model_id: %s",
                    model_id,
                )
            else:
                # CONF_TYPE is a measurement_key (old YAML-style entry)
                _LOGGER.debug(
                    "CONF_TYPE is a measurement_key (old entry): %s",
                    device_type,
                )

        _LOGGER.info(
            "Setting up Mobile Alerts device from config entry: device_id=%s, name=%s, model=%s",
            device_id,
            device_name,
            model_id,
        )

        # Create or reuse shared coordinator per phone_id
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        if "coordinators" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["coordinators"] = {}

        if phone_id not in hass.data[DOMAIN]["coordinators"]:
            # Create new API instance for new coordinator
            api = MobileAlertsApi(phone_id=phone_id)
            await api.register_device(device_id)
            coordinator = MobileAlertsCoordinator(hass, api)
            hass.data[DOMAIN]["coordinators"][phone_id] = coordinator
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("Created new coordinator for phone_id=%s", phone_id)
        else:
            # Reuse existing coordinator and API
            coordinator = hass.data[DOMAIN]["coordinators"][phone_id]
            # Register device and fetch its data
            await coordinator._api.register_device(device_id)
            _LOGGER.debug(
                "Reusing existing coordinator for phone_id=%s, registered device %s",
                phone_id,
                device_id,
            )

        # Get model info for this device
        model_info = DEVICE_MODELS.get(model_id, {})
        display_name = model_info.get("display_name", model_id)
        measurement_keys = model_info.get("measurement_keys", set())

        _LOGGER.debug(
            "Got model_info for %s (model_id=%s): display_name=%s, measurement_keys=%s",
            device_id,
            model_id,
            display_name,
            measurement_keys,
        )

        # Create DeviceInfo with model information
        device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Mobile Alerts",
            model=f"{model_id} - {display_name}",  # Now shows "MA10300 - Wireless Thermo-Hygrometer"
            serial_number=device_id,
        )

        _LOGGER.debug(
            "Created device info for %s: model=%s, name=%s, measurement_keys=%s",
            device_id,
            display_name,
            device_name,
            measurement_keys,
        )

        # Create entities based on device model's measurement keys
        entities: list[SensorEntity | BinarySensorEntity] = []

        # If no measurement_keys from model, but device_type is a measurement_key, use that (backward compat)
        if not measurement_keys and device_type and device_type in MEASUREMENT_TYPE_MAP:
            _LOGGER.debug(
                "Using device_type as measurement_key (old entry): %s",
                device_type,
            )
            measurement_keys = {device_type}

        # Create entities for each measurement key in the device model
        for measurement_key in measurement_keys:
            # For some models, the same API key has different meanings
            # E.g., MA10350: t2 = water level (not temperature like MA10300)
            # Check if this model has a sensor type override for this key
            sensor_type_override = get_sensor_type_override(model_id, measurement_key)
            sensor_type = (
                sensor_type_override if sensor_type_override else measurement_key
            )

            _LOGGER.debug(
                "Processing measurement_key %s for device %s (model %s, sensor_type %s)",
                measurement_key,
                device_id,
                model_id,
                sensor_type,
            )
            device_config = {
                CONF_DEVICE_ID: device_id,
                CONF_NAME: device_name,
                CONF_TYPE: sensor_type,  # Store sensor type (may be overridden, e.g., "water" for MA10350 t2)
            }

            _LOGGER.debug(
                "Created device_config for sensor_type %s: CONF_TYPE=%s",
                sensor_type,
                device_config.get(CONF_TYPE),
            )

            if sensor_type in MEASUREMENT_TYPE_MAP:
                sensor_class = MEASUREMENT_TYPE_MAP[sensor_type]
                entities.append(sensor_class(coordinator, device_config, device_info))
                _LOGGER.debug(
                    "Created sensor from model %s: %s (API key: %s)",
                    model_id,
                    sensor_type,
                    measurement_key,
                )
            else:
                _LOGGER.debug(
                    "Skipping measurement_key %s - sensor_type %s not in MEASUREMENT_TYPE_MAP",
                    measurement_key,
                    sensor_type,
                )

        # Special case: Wind direction has two sensors (text + degrees)
        if "wd" in measurement_keys:
            device_config_degrees = {
                CONF_DEVICE_ID: device_id,
                CONF_NAME: device_name,
                CONF_TYPE: "wd_degrees",
            }
            entities.append(
                MobileAlertsWindDirectionDegreesSensor(
                    coordinator, device_config_degrees, device_info
                )
            )
            _LOGGER.debug(
                "Created wind direction degrees sensor for model %s", model_id
            )

        # Add battery and last seen sensors
        entities.append(
            MobileAlertsBatterySensor(
                coordinator,
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_NAME: device_name,
                    CONF_TYPE: "battery",
                },
                device_info,
            )
        )
        entities.append(
            MobileAlertsLastSeenSensor(
                coordinator,
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_NAME: device_name,
                    CONF_TYPE: "last_seen",
                },
                device_info,
            )
        )

        add_entities(entities)
        _LOGGER.info(
            "Added %d sensor entities for device %s (model %s) from config entry %s",
            len(entities),
            device_id,
            model_id,
            config_entry.entry_id,
        )
    else:
        _LOGGER.warning("No device_id configured in config entry")
