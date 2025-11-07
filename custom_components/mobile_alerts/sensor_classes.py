"""Sensor entity classes for Mobile Alerts."""

from datetime import datetime, timezone
import logging
from typing import Final, cast

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
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_TYPE,
    PERCENTAGE,
    STATE_UNKNOWN,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import MobileAlertsCoordinator

_LOGGER: Final = logging.getLogger(__name__)


class MobileAlertsSensor(CoordinatorEntity, SensorEntity):
    """Base implementation of a Mobile Alerts sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator instance
            device: Device configuration dict with CONF_DEVICE_ID, CONF_NAME, CONF_TYPE
            device_info: Home Assistant DeviceInfo for this sensor
        """
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
        # Must stay in sync with MEASUREMENT_TYPE_MAP in sensor.py
        type_labels = {
            "t1": "Temperature T1",
            "t2": "Temperature T2",
            "t3": "Temperature T3",
            "t4": "Temperature T4",
            "h": "Humidity",
            "h1": "Humidity 1",
            "h2": "Humidity 2",
            "h3": "Humidity 3",
            "h4": "Humidity 4",
            "r": "Rain",
            "rf": "Rain Flow",
            "ws": "Wind Speed",
            "wg": "Wind Gust",
            "wd": "Wind Direction",
            "wd_degrees": "Wind Direction Degrees",
            "ap": "Air Pressure",
            "ppm": "Air Quality",
            "w": "Water",
            "battery": "Battery",
            "last_seen": "Last Seen",
            # Key press sensors (MA 10880 Wireless Switch)
            "kp1t": "Key Press 1 Type",
            "kp1c": "Key Press 1 Counter",
            "kp2t": "Key Press 2 Type",
            "kp2c": "Key Press 2 Counter",
            "kp3t": "Key Press 3 Type",
            "kp3c": "Key Press 3 Counter",
            "kp4t": "Key Press 4 Type",
            "kp4c": "Key Press 4 Counter",
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

    def extract_reading(self) -> None:
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


class MobileAlertsTemperatureSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts temperature sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the temperature sensor."""
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


class MobileAlertsHumiditySensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts humidity sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the humidity sensor."""
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


class MobileAlertsRainSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts rain sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the rain sensor."""
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


class MobileAlertsWindSpeedSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts wind speed sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the wind speed sensor."""
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
            if self._attr_native_value is None:
                return None
            # Convert string values from API to float
            return float(cast(int | float | str, self._attr_native_value))
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindDirectionSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts wind direction sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the wind direction sensor."""
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
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        try:
            if self._attr_native_value is None:
                return None
            val = int(cast(int | float | str, self._attr_native_value))
            if 0 <= val <= 15:
                return directions[val]
            return None
        except (ValueError, TypeError, IndexError):
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindDirectionDegreesSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts wind direction degrees sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the wind direction degrees sensor."""
        super().__init__(coordinator, device=device, device_info=device_info)
        self._device_class = None  # No device class for direction
        self._attr_native_unit_of_measurement = "°"
        self.entity_description = SensorEntityDescription(
            key="wind_direction_degrees",
            translation_key="wind_direction_degrees",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="°",
        )

    def extract_reading(self) -> None:
        """Extract wind direction data from coordinator (uses 'wd' key, not 'wd_degrees')."""
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

        # Wind direction degrees uses the "wd" measurement key
        if "wd" in measurement_data:
            state = measurement_data["wd"]
            available = True

        self._attr_native_value = state
        self._attr_available = available

        _LOGGER.debug(
            "MobileAlertsWindDirectionDegreesSensor::extract_reading %s %s:%s",
            self._attr_name,
            self._attr_native_value,
            self._attr_available,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor in degrees (0-337.5)."""
        try:
            if self._attr_native_value is None:
                return None
            val = int(cast(int | float | str, self._attr_native_value))
            if 0 <= val <= 15:
                # Calculate degrees: wd * 22.5
                return round(val * 22.5, 1)
            return None
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsWindGustSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts wind gust sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the wind gust sensor."""
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
            if self._attr_native_value is None:
                return None
            # Convert string values from API to float
            return float(cast(int | float | str, self._attr_native_value))
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid value for entity %s: %s",
                self.entity_id,
                self._attr_native_value,
            )
            return None


class MobileAlertsBatterySensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts battery sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
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

    def extract_reading(self) -> None:
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


class MobileAlertsLastSeenSensor(MobileAlertsSensor):
    """Implementation of a Mobile Alerts last seen sensor."""

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
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

    def extract_reading(self) -> None:
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


class MobileAlertsWaterSensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a Mobile Alerts water sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(
        self,
        coordinator: MobileAlertsCoordinator,
        device: dict[str, str],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the water sensor."""
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

    def extract_reading(self) -> None:
        """Extract reading from coordinator."""
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
