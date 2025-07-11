"""Support for the MobileAlerts service."""

from asyncio import timeout
from datetime import timedelta
import json
import logging
from typing import Any, Final, cast

import aiohttp
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
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_TYPE,
    PERCENTAGE,
    STATE_UNKNOWN,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import ATTRIBUTION, CONF_DEVICES, CONF_PHONE_ID

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
SCAN_INTERVAL = timedelta(minutes=10)

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
        # vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [cv.string])
    }
)


class ApiError(Exception):
    """Our custom ApiErrorException."""


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup."""

    phone_id = config.get(CONF_PHONE_ID, "")

    mad = MobileAlertsData(phone_id, config[CONF_DEVICES])
    coordinator = MobileAlertsCoordinator(hass, mad)

    await coordinator.async_refresh()
    sensors = []
    for device in config[CONF_DEVICES]:
        device_type = device[CONF_TYPE]
        if device_type in ["t1", "t2", "t3", "t4"]:
            sensors.append(MobileAlertsTemperatureSensor(coordinator, device))
        elif device_type in ["h", "h1", "h2", "h3", "h4"]:
            sensors.append(MobileAlertsHumiditySensor(coordinator, device))
        elif device_type in ["r"]:
            sensors.append(MobileAlertsRainSensor(coordinator, device))
        elif device_type in ["water"]:
            sensors.append(MobileAlertsWaterSensor(coordinator, device))
        else:
            sensors.append(MobileAlertsSensor(coordinator, device))
    add_entities(sensors)


# see https://developers.home-assistant.io/docs/integration_fetching_data/
class MobileAlertsCoordinator(DataUpdateCoordinator):
    """MobileAlerts implemented Coordinator."""

    def __init__(self, hass: HomeAssistant, mobile_alerts_data) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="MobileAlertsCoordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self._mobile_alerts_data = mobile_alerts_data

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            _LOGGER.debug("MobileAlertsCoordinator::_async_update_data")
            async with timeout(30):
                return await self._mobile_alerts_data.fetch_data()
        except ApiError as err:
            raise UpdateFailed("Error communicating with API") from err
        except:
            _LOGGER.warning(
                "Exception within MobileAlertsCoordinator::_async_update_data"
            )
            raise

    def get_reading(self, sensor_id: str) -> dict[str, Any] | None:
        """Extract sensor value from coordinator."""
        return self._mobile_alerts_data.get_reading(sensor_id)


class MobileAlertsSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device[CONF_DEVICE_ID]
        self._attr_name = device[CONF_NAME]

        self._type = device.get(CONF_TYPE, "t1")
        self._device_class = None
        self._id = self._device_id + self._type
        self._attr_unique_id = self._id

        self.extract_reading()
        self._attr_attribution = ATTRIBUTION

        _LOGGER.debug("MobileAlertsSensor::init ID %s", self._id)

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

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device)
        self._device_class = SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.HUMIDITY,
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

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device)
        self._device_class = SensorDeviceClass.PRECIPITATION
        self._attr_native_unit_of_measurement = UnitOfLength.MILLIMETERS
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.PRECIPITATION,
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


class MobileAlertsTemperatureSensor(
    MobileAlertsSensor, CoordinatorEntity, SensorEntity
):
    """Implementation of a MobileAlerts humidity sensor."""

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device)
        self._device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self.entity_description = SensorEntityDescription(
            key=SensorDeviceClass.TEMPERATURE,
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
    """Implementation of a MobileAlerts humidity sensor."""

    coordinator: MobileAlertsCoordinator

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_class = None
        self._type = "t2"
        self._attr_device_class = BinarySensorDeviceClass.MOISTURE
        self._device_id = device[CONF_DEVICE_ID]
        self._attr_name = device[CONF_NAME]
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


class MobileAlertsData:
    """Get the latest data from MobileAlerts.

    see REST API doc
    https://mobile-alerts.eu/de/home/
    https://mobile-alerts.eu/info/public_server_api_documentation.pdf
    """

    def __init__(self, phone_id: str, devices) -> None:
        """Init and register all passed devices."""
        self._phone_id = phone_id
        self._data = None
        self._device_ids = []
        for device in devices:
            self.register_device(device[CONF_DEVICE_ID])

    def register_device(self, device_id: str) -> None:
        """Register device in coordinator."""
        # _LOGGER.debug("MobileAlertsData::register_device {0}".format(device_id))
        if device_id in self._device_ids:
            return

        self._device_ids.append(device_id)
        _LOGGER.debug("device %s added - (%s)", device_id, self._device_ids)

    def get_reading(self, sensor_id: str) -> dict | None:
        """Return current data for the sensor.

        passed:
            sensor_id
        returns:
            json strcture of returned data
            None if the sensor isn't present
        """
        if self._data is None:
            # either still waiting for first call or calls have failed...
            _LOGGER.info("No sensor data")
            return None

        for sensor_data in self._data:
            if sensor_id == sensor_data["deviceid"]:
                return sensor_data

        _LOGGER.error("Sensor ID %s not found", sensor_id)
        return None

    async def fetch_data(self) -> None:
        """Fetch data from API."""
        try:
            _LOGGER.debug("MobileAlertsData::fetch_data")
            if len(self._device_ids) == 0:
                _LOGGER.debug("no device ids registered")
                return

            url = "https://www.data199.com/api/pv1/device/lastmeasurement"
            headers = {"Content-Type": "application/json"}
            request_data = {"deviceids": ",".join(self._device_ids)}
            json_data = json.dumps(request_data)
            # todo add phoneid if it's there
            #        if len(self._phone_id) > 0:
            #            data["phoneid"] = self._phone_id

            _LOGGER.debug("data %s", json_data)

            page_text = ""
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as session,
                session.post(url, data=json_data, headers=headers) as response,
            ):
                page_text = await response.read()
                if response.status != 200:
                    _LOGGER.error(
                        "POST error: %s, %s, %s", response.status, url, request_data
                    )

            sensor_response = json.loads(page_text)
            # check data returned has no errors
            if not sensor_response["success"]:
                _LOGGER.warning(
                    "Error getting data from MA %s:%s",
                    sensor_response["errorcode"],
                    sensor_response["errormessage"],
                )
                self._data = None
                return
            if sensor_response is None:
                _LOGGER.warning("Failed to fetch data from OWM")
                return

            if "devices" not in sensor_response:
                _LOGGER.warning("MA data contains no devices %s", sensor_response)
                return

            self._data = sensor_response["devices"]

        except ConnectionError as e:
            _LOGGER.warning("Unable to connect to MA URL")
            raise ApiError from e
        except TimeoutError as e:
            _LOGGER.warning("Timeout connecting to MA URL")
            raise ApiError from e
        except Exception as e:
            _LOGGER.warning("%s occurred details: %s", e.__class__, e)
            raise ApiError from e
