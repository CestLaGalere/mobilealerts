"""Support for the MobileAlerts service."""

from asyncio import timeout
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Final

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ApiError, MobileAlertsApi
from .const import (
    ATTRIBUTION,
    CONF_DEVICES,
    CONF_PHONE_ID,
    DEVICE_TYPE_AIR_QUALITY,
    DEVICE_TYPE_CABLE_TEMPERATURE,
    DEVICE_TYPE_EXTERNAL_HUMIDITY,
    DEVICE_TYPE_HUMIDITY,
    DEVICE_TYPE_PRESSURE,
    DEVICE_TYPE_RAIN,
    DEVICE_TYPE_TEMPERATURE,
    DEVICE_TYPE_WINDOW,
    DEVICE_TYPE_WIND,
    DOMAIN,
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
    SCAN_INTERVAL_MINUTES,
    SENSORS,
    detect_device_type,
)

_LOGGER: Final = logging.getLogger(__name__)

# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Mobile Alerts sensors from YAML configuration.

    This is the active method for YAML-based setup.
    The config parameter contains the platform configuration directly.
    """
    _LOGGER.debug("async_setup_platform called for Mobile Alerts YAML setup")
    _LOGGER.debug("Platform config received: %s", config)

    # The config is passed directly from YAML sensor platform configuration
    phone_id = config.get(CONF_PHONE_ID, "")
    devices_config = config.get(CONF_DEVICES, [])

    _LOGGER.info(
        "Setting up Mobile Alerts sensors from YAML platform: phone_id=%s, %d device(s)",
        phone_id if phone_id else "(empty)",
        len(devices_config),
    )

    if not devices_config:
        _LOGGER.warning("No devices configured in YAML platform config")
        return

    # Initialize API with phone_id
    api = MobileAlertsApi(phone_id=phone_id if phone_id else "")

    # Register all devices with API
    for device_config in devices_config:
        device_id = device_config.get(CONF_DEVICE_ID)
        if device_id:
            api.register_device(device_id)

    # Create coordinator
    coordinator = MobileAlertsCoordinator(hass, api)

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Create sensors for each device
    entities_to_add = []

    for device_config in devices_config:
        device_id = device_config.get(CONF_DEVICE_ID)
        device_name = device_config.get(CONF_NAME, f"Device {device_id}")
        device_type = device_config.get(CONF_TYPE, "")

        if not device_id:
            _LOGGER.warning("Device configuration missing device_id, skipping")
            continue

        _LOGGER.debug(
            "Creating sensors for device: id=%s, name=%s, type=%s",
            device_id,
            device_name,
            device_type,
        )

        # Create sensor for each sensor type in SENSORS list
        for description in SENSORS:
            # Check if this sensor should be created for this device type
            if should_create_sensor(description.key, device_type):
                entity = MobileAlertsSensorEntity(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    description=description,
                )
                entities_to_add.append(entity)
                _LOGGER.debug(
                    "Added sensor entity: %s (unique_id=%s)",
                    entity.entity_id,
                    entity.unique_id,
                )

    # Add all entities at once
    if entities_to_add:
        add_entities(entities_to_add)
        _LOGGER.info(
            "Added %d sensor entities for %d device(s)",
            len(entities_to_add),
            len(devices_config),
        )
    else:
        _LOGGER.warning("No sensor entities created for configured devices")


# CONFIG FLOW SETUP DEACTIVATED FOR NOW - UNTIL YAML WORKS
# This will be re-enabled in a later step

# async def async_setup_entry(
#     hass: HomeAssistant,
#     config_entry,
#     async_add_entities: AddEntitiesCallback,
# ) -> None:
#     """Set up Mobile Alerts sensors from a config entry - DEACTIVATED."""
#     _LOGGER.debug("async_setup_entry called but DEACTIVATED")
#     return


def should_create_sensor(entity_type: str, device_type: str) -> bool:
    """Check if sensor should be created for this device type.

    Based on API documentation sensor IDs and their capabilities.
    Only creates sensors that are actually supported by the device type.
    """
    # Battery and Last Seen always created for all devices
    if entity_type in (ENTITY_TYPE_BATTERY, ENTITY_TYPE_LAST_SEEN):
        return True

    # If device_type is empty, don't create any sensors (unknown device)
    # This shouldn't happen after detection, but handle it gracefully
    if not device_type:
        return False

    # Temperature - all temperature sensor types have t1
    if (
        entity_type == ENTITY_TYPE_TEMPERATURE
        and device_type in DEVICE_TYPE_TEMPERATURE
    ):
        return True

    # Cable/external temperature (t2) - ID01, ID04, ID06, ID09, ID0F, ID17
    if (
        entity_type == ENTITY_TYPE_CABLE_TEMPERATURE
        and device_type in DEVICE_TYPE_CABLE_TEMPERATURE
    ):
        return True

    # Humidity - all humidity sensor types have h
    if entity_type == ENTITY_TYPE_HUMIDITY and device_type in DEVICE_TYPE_HUMIDITY:
        return True

    # External humidity (h2) - ID07 only
    if (
        entity_type == ENTITY_TYPE_EXTERNAL_HUMIDITY
        and device_type in DEVICE_TYPE_EXTERNAL_HUMIDITY
    ):
        return True

    # Rain - ID08 only
    if entity_type == ENTITY_TYPE_RAIN and device_type in DEVICE_TYPE_RAIN:
        return True

    # Wind speed and gust - ID0B only
    if (
        entity_type in (ENTITY_TYPE_WIND_SPEED, ENTITY_TYPE_WIND_GUST)
        and device_type in DEVICE_TYPE_WIND
    ):
        return True

    # Air pressure - ID18 only
    if entity_type == ENTITY_TYPE_PRESSURE and device_type in DEVICE_TYPE_PRESSURE:
        return True

    # Air quality (PPM) - ID05 only
    if (
        entity_type == ENTITY_TYPE_AIR_QUALITY
        and device_type in DEVICE_TYPE_AIR_QUALITY
    ):
        return True

    # Window status - ID10 only
    if entity_type == ENTITY_TYPE_WINDOW and device_type in DEVICE_TYPE_WINDOW:
        return True

    return False


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
        """Fetch data from API endpoint."""
        try:
            _LOGGER.debug("MobileAlertsCoordinator::_async_update_data")
            async with timeout(30):
                await self._api.fetch_data()
                return self._api
        except ApiError as err:
            raise UpdateFailed("Error communicating with API") from err

    def get_reading(self, device_id: str) -> dict[str, Any] | None:
        """Extract sensor value from coordinator."""
        return self._api.get_reading(device_id)


class MobileAlertsSensorEntity(CoordinatorEntity, SensorEntity):
    """Mobile Alerts sensor entity."""

    coordinator: MobileAlertsCoordinator

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device_id: str,
        device_name: str,
        device_type: str,
        description,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_type = device_type
        self._description = description

        # Build unique ID
        self._attr_unique_id = f"{device_id}_{description.key}"

        # Set name: device_name + suffix (e.g., " Battery", " Last Seen")
        self._attr_name = f"{device_name}{description.suffix}".strip()

        # Set entity description attributes
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_attribution = ATTRIBUTION

        self.extract_reading()

        _LOGGER.debug(
            "Sensor initialized: %s (unique_id=%s)",
            self._attr_name,
            self._attr_unique_id,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.extract_reading()
        self.async_write_ha_state()

    def extract_reading(self) -> None:
        """Extract sensor value from coordinator."""
        data = self.coordinator.get_reading(self._device_id)
        self._attr_available = False

        if data is None:
            self._attr_native_value = None
            return

        if "measurement" not in data:
            self._attr_native_value = None
            return

        measurement_data = data.get("measurement", {})
        measurement_key = self._description.measurement_key

        # Extract the specific measurement value
        if measurement_key in measurement_data:
            value = measurement_data[measurement_key]
            self._process_value(value)
            self._attr_available = True
        else:
            self._attr_native_value = None

        _LOGGER.debug(
            "Sensor %s: value=%s, available=%s",
            self._attr_unique_id,
            self._attr_native_value,
            self._attr_available,
        )

    def _process_value(self, value: Any) -> None:
        """Process the raw value based on entity type."""
        entity_type = self._description.key

        if entity_type == ENTITY_TYPE_TEMPERATURE:
            self._process_temperature(value)
        elif entity_type == ENTITY_TYPE_CABLE_TEMPERATURE:
            self._process_temperature(value)
        elif entity_type == ENTITY_TYPE_HUMIDITY:
            self._process_humidity(value)
        elif entity_type == ENTITY_TYPE_EXTERNAL_HUMIDITY:
            self._process_humidity(value)
        elif entity_type == ENTITY_TYPE_RAIN:
            self._process_rain(value)
        elif entity_type == ENTITY_TYPE_WIND_SPEED:
            self._process_wind_speed(value)
        elif entity_type == ENTITY_TYPE_WIND_GUST:
            self._process_wind_speed(value)
        elif entity_type == ENTITY_TYPE_PRESSURE:
            self._process_pressure(value)
        elif entity_type == ENTITY_TYPE_AIR_QUALITY:
            self._process_air_quality(value)
        elif entity_type == ENTITY_TYPE_WINDOW:
            self._process_window(value)
        elif entity_type == ENTITY_TYPE_BATTERY:
            self._process_battery(value)
        elif entity_type == ENTITY_TYPE_LAST_SEEN:
            self._process_timestamp(value)
        else:
            self._attr_native_value = value

    def _process_temperature(self, value: Any) -> None:
        """Process temperature value with validation."""
        try:
            val = float(str(value))
            if -100 <= val <= 100:
                self._attr_native_value = val
            else:
                _LOGGER.warning(
                    "Temperature %s out of range for %s", val, self._attr_unique_id
                )
                self._attr_native_value = None
        except ValueError:
            _LOGGER.warning(
                "Invalid temperature value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_humidity(self, value: Any) -> None:
        """Process humidity value with validation."""
        try:
            val = float(str(value))
            if 0 <= val <= 100:
                self._attr_native_value = val
            else:
                _LOGGER.warning(
                    "Humidity %s out of range for %s", val, self._attr_unique_id
                )
                self._attr_native_value = None
        except ValueError:
            _LOGGER.warning(
                "Invalid humidity value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_rain(self, value: Any) -> None:
        """Process rain value (in mm)."""
        try:
            self._attr_native_value = float(str(value))
        except ValueError:
            _LOGGER.warning(
                "Invalid rain value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_wind_speed(self, value: Any) -> None:
        """Process wind speed/gust value (in m/s)."""
        try:
            self._attr_native_value = float(str(value))
        except ValueError:
            _LOGGER.warning(
                "Invalid wind value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_pressure(self, value: Any) -> None:
        """Process air pressure value (in hPa)."""
        try:
            self._attr_native_value = float(str(value))
        except ValueError:
            _LOGGER.warning(
                "Invalid pressure value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_air_quality(self, value: Any) -> None:
        """Process air quality/PPM value."""
        try:
            self._attr_native_value = float(str(value))
        except ValueError:
            _LOGGER.warning(
                "Invalid air quality value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_window(self, value: Any) -> None:
        """Process window status (boolean or text)."""
        try:
            # Convert to boolean: false = closed, true = open
            val = float(str(value))
            self._attr_native_value = bool(val)
        except ValueError:
            _LOGGER.warning(
                "Invalid window value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_battery(self, value: Any) -> None:
        """Process battery value with validation."""
        try:
            val = float(str(value))
            if 0 <= val <= 100:
                self._attr_native_value = val
            else:
                _LOGGER.warning(
                    "Battery %s out of range for %s", val, self._attr_unique_id
                )
                self._attr_native_value = None
        except ValueError:
            _LOGGER.warning(
                "Invalid battery value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None

    def _process_timestamp(self, value: Any) -> None:
        """Process timestamp value."""
        try:
            # Value is a Unix timestamp in seconds
            timestamp = int(str(value))
            # Convert to datetime
            self._attr_native_value = datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError, OSError):
            _LOGGER.warning(
                "Invalid timestamp value for %s: %s", self._attr_unique_id, value
            )
            self._attr_native_value = None
