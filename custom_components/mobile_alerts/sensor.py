"""Support for the MobileAlerts service."""

from datetime import timedelta, datetime, timezone
import logging
from typing import Any, Final, cast

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.weather import PLATFORM_SCHEMA as WEATHER_PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_TYPE,
    PERCENTAGE,
    STATE_UNKNOWN,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MobileAlertsApi
from .const import (
    ATTRIBUTION,
    CONF_DEVICES,
    CONF_PHONE_ID,
    DOMAIN,
    SCAN_INTERVAL_MINUTES,
)

SensorAttributes = dict[str, any]

_LOGGER: Final = logging.getLogger(__name__)


SENSOR_READINGS = [
    "temperature",
    "winddirection",
    "windbearing",
    "windspeed",
    "gust",
    "humidity",
    "pressure",
    "rain",
    "snow",
]

# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TYPE): cv.string,
    }
)

PLATFORM_SCHEMA = WEATHER_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_PHONE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup from YAML configuration."""
    _LOGGER.debug("async_setup_platform called for Mobile Alerts YAML setup")

    phone_id = config.get(CONF_PHONE_ID, "")
    devices_config = config.get(CONF_DEVICES, [])

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
        api.register_device(device_id)

        # Create device info for each unique device_id (only once per device)
        if device_id not in device_info_map:
            # Use device_name directly from first occurrence in config
            # Don't try to strip suffixes - the user knows their device names best
            device_name = device[CONF_NAME]

            device_info_map[device_id] = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=device_name,
                manufacturer="Mobile Alerts",
                model="Mobile Alerts Sensor",
                serial_number=device_id,
            )
            _LOGGER.debug(
                "Created device info for device_id=%s, name=%s", device_id, device_name
            )

    # Create coordinator
    coordinator = MobileAlertsCoordinator(hass, api)
    await coordinator.async_refresh()

    sensors = []
    processed_device_ids = set()

    for device in devices_config:
        device_type = device[CONF_TYPE]
        device_id = device[CONF_DEVICE_ID]

        # Create the main sensor based on device type
        if device_type in ["t1", "t2", "t3", "t4"]:
            sensors.append(
                MobileAlertsTemperatureSensor(
                    coordinator, device, device_info_map[device_id]
                )
            )
        elif device_type in ["h", "h1", "h2", "h3", "h4"]:
            sensors.append(
                MobileAlertsHumiditySensor(
                    coordinator, device, device_info_map[device_id]
                )
            )
        elif device_type in ["r"]:
            sensors.append(
                MobileAlertsRainSensor(coordinator, device, device_info_map[device_id])
            )
        elif device_type in ["water"]:
            sensors.append(
                MobileAlertsWaterSensor(coordinator, device, device_info_map[device_id])
            )
        else:
            sensors.append(
                MobileAlertsSensor(coordinator, device, device_info_map[device_id])
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

    # Check if this is a device-based entry or YAML-migration entry
    device_id = entry_data.get(CONF_DEVICE_ID)

    if device_id:
        # Single device entry (from config_flow or YAML migration)
        device_name = entry_data.get(CONF_NAME, f"Device {device_id}")
        device_type = entry_data.get(CONF_TYPE, "")

        _LOGGER.info(
            "Setting up Mobile Alerts sensor from config entry: device_id=%s, name=%s, type=%s",
            device_id,
            device_name,
            device_type,
        )

        # Create API instance
        api = MobileAlertsApi(phone_id=phone_id if phone_id else "")

        # Register device
        api.register_device(device_id)

        # Create coordinator
        coordinator = MobileAlertsCoordinator(hass, api)

        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()

        # Create DeviceInfo
        device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Mobile Alerts",
            model="Mobile Alerts Sensor",
            serial_number=device_id,
        )

        # Create entities based on device type
        entities: list[SensorEntity | BinarySensorEntity] = []

        # Get the actual measurement data to know which entities to create
        device_reading = coordinator.get_reading(device_id)
        measurement = device_reading.get("measurement", {}) if device_reading else {}

        _LOGGER.debug(
            "Creating entities for device %s with measurement keys: %s",
            device_id,
            list(measurement.keys()) if measurement else [],
        )

        # Create entities for each measurement key found
        measurement_type_map = {
            "t1": (MobileAlertsTemperatureSensor, "Temperature T1"),
            "t2": (MobileAlertsTemperatureSensor, "Temperature T2"),
            "t3": (MobileAlertsTemperatureSensor, "Temperature T3"),
            "t4": (MobileAlertsTemperatureSensor, "Temperature T4"),
            "h": (MobileAlertsHumiditySensor, "Humidity"),
            "h2": (MobileAlertsHumiditySensor, "Humidity 2"),
            "h3": (MobileAlertsHumiditySensor, "Humidity 3"),
            "h4": (MobileAlertsHumiditySensor, "Humidity 4"),
            "r": (MobileAlertsRainSensor, "Rain"),
            "rf": (MobileAlertsRainSensor, "Rain Flow"),
            "ws": (MobileAlertsWindSpeedSensor, "Wind Speed"),
            "wg": (MobileAlertsWindGustSensor, "Wind Gust"),
            "wd": (MobileAlertsWindDirectionSensor, "Wind Direction"),
            "ap": (MobileAlertsTemperatureSensor, "Air Pressure"),
            "ppm": (MobileAlertsTemperatureSensor, "Air Quality"),
            "w": (MobileAlertsTemperatureSensor, "Window"),
        }

        # Create sensors for each measurement type found in the data
        for meas_key in measurement.keys():
            # Skip metadata keys
            if meas_key in ["idx", "ts", "c", "lb"]:
                continue
            # Skip alert flag keys
            if any(
                meas_key.endswith(suffix)
                for suffix in [
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
            ):
                continue

            # Check if this is a known measurement type
            if meas_key in measurement_type_map:
                sensor_class, display_name = measurement_type_map[meas_key]
                device_dict = {
                    CONF_DEVICE_ID: device_id,
                    CONF_NAME: f"{device_name}",
                    CONF_TYPE: meas_key,
                }
                try:
                    entities.append(
                        sensor_class(
                            coordinator=coordinator,
                            device=device_dict,
                            device_info=device_info,
                        )
                    )
                    _LOGGER.debug(
                        "Created %s entity for device %s (measurement key: %s)",
                        sensor_class.__name__,
                        device_id,
                        meas_key,
                    )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error(
                        "Error creating sensor for measurement key %s: %s",
                        meas_key,
                        err,
                    )

        # Battery and Last Seen sensors (for all device types)
        device_dict_battery = {
            CONF_DEVICE_ID: device_id,
            CONF_NAME: f"{device_name}",
            CONF_TYPE: "battery",
        }
        entities.append(
            MobileAlertsBatterySensor(
                coordinator=coordinator,
                device=device_dict_battery,
                device_info=device_info,
            )
        )

        device_dict_lastseen = {
            CONF_DEVICE_ID: device_id,
            CONF_NAME: f"{device_name}",
            CONF_TYPE: "last_seen",
        }
        entities.append(
            MobileAlertsLastSeenSensor(
                coordinator=coordinator,
                device=device_dict_lastseen,
                device_info=device_info,
            )
        )

        add_entities(entities)

        _LOGGER.debug("Added %d entities for device %s", len(entities), device_id)
    else:
        # Multi-device entry (from YAML config)
        devices_config = entry_data.get(CONF_DEVICES, [])

        if devices_config:
            _LOGGER.info(
                "Setting up Mobile Alerts sensors from config entry: phone_id=%s, %d device(s)",
                phone_id if phone_id else "(empty)",
                len(devices_config),
            )

            # Call the existing YAML setup logic
            await async_setup_platform(
                hass,
                {
                    CONF_PHONE_ID: phone_id,
                    CONF_DEVICES: devices_config,
                },
                add_entities,
            )
        else:
            _LOGGER.warning("No devices configured in config entry")


# see https://developers.home-assistant.io/docs/integration_fetching_data/
class MobileAlertsCoordinator(DataUpdateCoordinator):
    """MobileAlerts implemented Coordinator."""

    def __init__(self, hass: HomeAssistant, api: MobileAlertsApi) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="MobileAlertsCoordinator",
            update_interval=SCAN_INTERVAL,
        )
        self._api = api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            _LOGGER.debug("MobileAlertsCoordinator::_async_update_data")
            return await self._api.fetch_data()
        except Exception as err:
            raise UpdateFailed("Error communicating with API") from err

    def get_reading(self, sensor_id: str) -> dict[str, Any] | None:
        """Extract sensor value from coordinator."""
        return self._api.get_reading(sensor_id)


class MobileAlertsSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device[CONF_DEVICE_ID]
        self._device_name = device[CONF_NAME]
        self._attr_device_info = device_info

        self._type = device.get(CONF_TYPE, "t1")
        self._device_class = None
        self._id = self._device_id + self._type
        self._attr_unique_id = self._id

        # Set display name based on sensor type
        # This makes entity IDs more descriptive like "sensor.test1_temperature_t1"
        type_labels = {
            "t1": "Temperature T1",
            "t2": "Temperature T2",
            "t3": "Temperature T3",
            "t4": "Temperature T4",
            "h": "Humidity",
            "h2": "Humidity 2",
            "h3": "Humidity 3",
            "h4": "Humidity 4",
            "r": "Rain",
            "rf": "Rain Flow",
            "ws": "Wind Speed",
            "wg": "Wind Gust",
            "wd": "Wind Direction",
            "ap": "Air Pressure",
            "ppm": "Air Quality",
            "w": "Window",
            "battery": "Battery",
            "last_seen": "Last Seen",
        }

        type_label = type_labels.get(self._type, self._type.upper())
        self._attr_name = f"{self._device_name} {type_label}"

        self.extract_reading()
        self._attr_attribution = ATTRIBUTION

        _LOGGER.debug(
            "MobileAlertsSensor::init ID %s, name=%s", self._id, self._attr_name
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.extract_reading()
        self.async_write_ha_state()

    def extract_reading(self):
        """Extract sensor value from coordinator."""
        data = self.coordinator.get_reading(self._device_id)
        self._attr_extra_state_attributes = data if data is not None else {}
        self._attr_native_value = None
        self._attr_available = False
        if data is None:
            return
        if "measurement" not in data:
            return

        measurement_data = data["measurement"]
        state = STATE_UNKNOWN
        available = False

        if len(self._type) == 0:
            # run through measurements to get first non date one and use this
            for measurement, value in measurement_data.items():
                if measurement in ["idx", "ts", "c"]:
                    continue
                state = value
                available = True
                break
        elif self._type in measurement_data:
            state = measurement_data[self._type]
            available = True

        self._attr_native_value = state
        self._attr_available = available

        _LOGGER.debug(
            "MobileAlertsSensor::extract_reading %s %s:%s",
            self._attr_name,
            self._attr_native_value,
            self._attr_available,
        )


class MobileAlertsHumiditySensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts humidity sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.HUMIDITY,
            translation_key="humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        if self._attr_native_value is None:
            return None
        try:
            val = float(str(self._attr_native_value))
            if val > 100 or val < 0:
                return None
            return val
        except ValueError:
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsRainSensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts rain sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = SensorDeviceClass.PRECIPITATION
        self._attr_native_unit_of_measurement = UnitOfLength.MILLIMETERS
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.PRECIPITATION,
            translation_key="rain",
            device_class=SensorDeviceClass.PRECIPITATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        try:
            return cast(float, self._attr_native_value)
        except ValueError:
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindSpeedSensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts wind speed sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = SensorDeviceClass.WIND_SPEED
        self._attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.WIND_SPEED,
            translation_key="wind_speed",
            device_class=SensorDeviceClass.WIND_SPEED,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        try:
            return cast(float, self._attr_native_value)
        except ValueError:
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindDirectionSensor(
    MobileAlertsSensor, CoordinatorEntity, SensorEntity
):
    """Implementation of a MobileAlerts wind direction sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = None  # No device class for direction
        self._attr_native_unit_of_measurement = None
        self.entity_description = SensorEntityDescription(
            key="wind_direction",
            translation_key="wind_direction",
            device_class=None,
            state_class=None,
            native_unit_of_measurement=None,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor (0-15 for compass directions)."""
        try:
            if self._attr_native_value is None:
                return None
            val = int(cast(int | float | str, self._attr_native_value))
            if 0 <= val <= 15:
                return val
            return None
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindGustSensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts wind gust sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = None  # Wind gust doesn't have a device class in HA
        self._attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
        self.entity_description = SensorEntityDescription(
            key="wind_gust",
            translation_key="wind_gust",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        try:
            return cast(float, self._attr_native_value)
        except ValueError:
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsTemperatureSensor(
    MobileAlertsSensor, CoordinatorEntity, SensorEntity
):
    """Implementation of a MobileAlerts temperature sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.TEMPERATURE,
            translation_key="temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        if self._attr_native_value is None:
            return None
        try:
            val = float(str(self._attr_native_value))
            if val > 100 or val < -100:
                return None
            return val
        except ValueError:
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWaterSensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a MobileAlerts water sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_class = None
        self._type = "t2"
        self._attr_device_class = BinarySensorDeviceClass.MOISTURE
        self._device_id = device[CONF_DEVICE_ID]
        self._attr_name = device[CONF_NAME]
        self._attr_device_info = device_info
        self._id = self._device_id + self._type
        self._attr_unique_id = self._id
        self.extract_reading()
        self._attr_attribution = ATTRIBUTION

        _LOGGER.debug("MobileAlertsWaterSensor::init ID %s", self._id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.extract_reading()
        self.async_write_ha_state()

    def extract_reading(self):
        """Extract reading to from coordinator."""
        data = self.coordinator.get_reading(self._device_id)
        self._attr_extra_state_attributes = data if data is not None else {}
        self._attr_available = False
        if data is None:
            return
        if "measurement" not in data:
            return

        measurement_data = data["measurement"]
        state = STATE_UNKNOWN
        available = False

        if len(self._type) == 0:
            # run through measurements to get first non date one and use this
            for measurement, value in measurement_data.items():
                if measurement in ["idx", "ts", "c"]:
                    continue
                state = value
                available = True
                break
        elif self._type in measurement_data:
            state = measurement_data[self._type]
            available = True

        if state is not None:
            self._attr_is_on = int(state) == 1
        self._attr_available = available

        _LOGGER.debug(
            "MobileAlertsWaterSensor::extract_reading %s %s:%s",
            self._attr_name,
            self._attr_is_on,
            self._attr_available,
        )


class MobileAlertsBatterySensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts battery sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the battery sensor."""
        # Create a copy of device config with type for battery
        # Don't modify the name - the base class will add the type label
        battery_device = device.copy()
        battery_device[CONF_TYPE] = "battery"

        super().__init__(coordinator, device=battery_device, device_info=device_info)
        # Override unique_id to include sensor type to avoid conflicts
        self._attr_unique_id = f"{device[CONF_DEVICE_ID]}_battery"
        # Use generic sensor without device class for string values
        self._device_class = None
        self._attr_native_unit_of_measurement = None
        # Set battery icon manually since we can't use device_class=BATTERY with string values
        self._attr_icon = "mdi:battery"
        self.entity_description = SensorEntityDescription(
            key="battery_status",
            device_class=None,  # No device class for string-based status
            state_class=None,  # String values don't have state class
            native_unit_of_measurement=None,
            icon="mdi:battery",
        )

    def extract_reading(self):
        """Extract battery status from coordinator."""
        data = self.coordinator.get_reading(self._device_id)
        self._attr_extra_state_attributes = data if data is not None else {}
        self._attr_native_value = None
        self._attr_available = False

        if data is None:
            return
        if "measurement" not in data:
            return

        measurement_data = data["measurement"]

        # Check for lowbattery field in the API response
        if "lowbattery" in measurement_data:
            try:
                low_battery = measurement_data["lowbattery"]

                # Convert boolean or string to battery status
                if isinstance(low_battery, bool):
                    self._attr_native_value = "Low" if low_battery else "OK"
                elif isinstance(low_battery, str):
                    # Handle string values like "true"/"false"
                    if low_battery.lower() in ["true", "1", "yes"]:
                        self._attr_native_value = "Low"
                    else:
                        self._attr_native_value = "OK"
                else:
                    # Fallback for other types
                    self._attr_native_value = "Low" if low_battery else "OK"

                # Set dynamic icon based on battery status
                if self._attr_native_value == "Low":
                    self._attr_icon = "mdi:battery-low"
                else:
                    self._attr_icon = "mdi:battery"

                self._attr_available = True

            except (ValueError, TypeError):
                self._attr_native_value = "Unknown"
                self._attr_icon = "mdi:battery-unknown"
                self._attr_available = True
        else:
            # If no lowbattery field found, assume OK
            self._attr_native_value = "OK"
            self._attr_icon = "mdi:battery"
            self._attr_available = True

        _LOGGER.debug(
            "MobileAlertsBatterySensor::extract_reading %s %s:%s",
            self._attr_name,
            self._attr_native_value,
            self._attr_available,
        )


class MobileAlertsLastSeenSensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts last seen sensor."""

    def __init__(
        self, coordinator, device: dict[str, str], device_info: DeviceInfo
    ) -> None:
        """Initialize the last seen sensor."""
        # Create a copy of device config with type for last seen
        # Don't modify the name - the base class will add the type label
        last_seen_device = device.copy()
        last_seen_device[CONF_TYPE] = "last_seen"

        super().__init__(coordinator, device=last_seen_device, device_info=device_info)
        # Override unique_id to include sensor type to avoid conflicts
        self._attr_unique_id = f"{device[CONF_DEVICE_ID]}_last_seen"
        self._device_class = SensorDeviceClass.TIMESTAMP
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.TIMESTAMP,
            translation_key="last_seen",
            device_class=SensorDeviceClass.TIMESTAMP,
            state_class=None,  # Timestamps don't have state class
        )

    def extract_reading(self):
        """Extract last seen timestamp from coordinator."""
        data = self.coordinator.get_reading(self._device_id)
        self._attr_extra_state_attributes = data if data is not None else {}
        self._attr_native_value = None
        self._attr_available = False

        if data is None:
            return
        if "measurement" not in data:
            return

        measurement_data = data["measurement"]

        # Last seen is in 'c' field (when sensor last transmitted to receiver)
        if "c" in measurement_data:
            try:
                # 'c' should be a timestamp
                timestamp_value = measurement_data["c"]

                # Convert timestamp to datetime object with timezone
                if isinstance(timestamp_value, (int, float)):
                    # Unix timestamp - add UTC timezone
                    self._attr_native_value = datetime.fromtimestamp(
                        timestamp_value, tz=timezone.utc
                    )
                elif isinstance(timestamp_value, str):
                    # ISO string or other format
                    try:
                        # Try parsing as ISO format first
                        dt = datetime.fromisoformat(timestamp_value)
                        # If no timezone info, assume UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        self._attr_native_value = dt
                    except ValueError:
                        # Try parsing as unix timestamp string
                        unix_ts = float(timestamp_value)
                        self._attr_native_value = datetime.fromtimestamp(
                            unix_ts, tz=timezone.utc
                        )

                self._attr_available = True

            except (ValueError, TypeError, OSError) as e:
                _LOGGER.warning(
                    "Could not parse last seen timestamp %s: %s",
                    measurement_data.get("c"),
                    e,
                )
                self._attr_native_value = None
                self._attr_available = False

        _LOGGER.debug(
            "MobileAlertsLastSeenSensor::extract_reading %s %s:%s",
            self._attr_name,
            self._attr_native_value,
            self._attr_available,
        )
