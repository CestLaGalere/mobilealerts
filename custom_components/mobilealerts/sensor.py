"""Support for the MobileAlerts service."""
from datetime import timedelta
import logging
from typing import Optional, cast
import json

from homeassistant.core import callback

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

import async_timeout
import aiohttp

import voluptuous as vol

from .const import (
    CONF_DEVICES,
    CONF_PHONE_ID,
    ATTRIBUTION,
)

from homeassistant.components.weather import (
    PLATFORM_SCHEMA,
)

from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    CONF_NAME,
    CONF_TYPE,
    CONF_DEVICE_ID,
    STATE_UNKNOWN,
)

from homeassistant.helpers.typing import (
    ConfigType,
    StateType,
    HomeAssistantType,
)

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass

SensorAttributes = dict[str, any]

_LOGGER = logging.getLogger(__name__)

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
        vol.Required(CONF_TYPE): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_PHONE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [SENSOR_SCHEMA])
        # vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [cv.string])
    }
)


class ApiError(Exception):
    ...
    pass


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        add_entities: AddEntitiesCallback
) -> None:
    session = async_get_clientsession(hass)

    phone_id = ""
    if CONF_PHONE_ID in config:
        phone_id = config.get(CONF_PHONE_ID)

    mad = MobileAlertsData(phone_id, config[CONF_DEVICES])
    coordinator = MobileAlertsCoordinator(hass, mad)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()
    sensors = []
    for device in config[CONF_DEVICES]:
        device_type = device[CONF_TYPE]
        if device_type in ["t1", "t2", "t3", "t4"]:
            sensors.append(MobileAlertsTemperatureSensor(coordinator, device))
        elif device_type in ["h", "h1", "h2", "h3", "h4"]:
            sensors.append(MobileAlertsHumiditySensor(coordinator, device))
        else:
            sensors.append(MobileAlertsSensor(coordinator, device))
    add_entities(sensors)


# see https://developers.home-assistant.io/docs/integration_fetching_data/
class MobileAlertsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, mobile_alerts_data):
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
            async with async_timeout.timeout(30):
                return await self._mobile_alerts_data.fetch_data()
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except:
            _LOGGER.warning('Exception within MobileAlertsCoordinator::_async_update_data')
            raise

    def get_reading(self, sensor_id: str) -> Optional[dict]:
        return self._mobile_alerts_data.get_reading(sensor_id)


class MobileAlertsSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts sensor. """

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device[CONF_DEVICE_ID]
        self._attr_name = device[CONF_NAME]

        if CONF_TYPE in device:
            self._type = device[CONF_TYPE]
        else:
            self._type = "t1"
        self._device_class = None
        self._id = self._device_id + self._type
        self._attr_unique_id = self._id

        self.extract_reading()
        self._attr_attribution = ATTRIBUTION

        _LOGGER.debug("MobileAlertsSensor::init ID {0}".format(self._id))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.extract_reading()
        self.async_write_ha_state()

    def extract_reading(self):
        data = self.coordinator.get_reading(self._device_id)
        self._attr_extra_state_attributes = data
        self._attr_state = STATE_UNKNOWN
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

        self._attr_state = state
        self._attr_available = available

        _LOGGER.debug("MobileAlertsSensor::_handle_coordinator_update {0} {1}:{2}".format(self._attr_name,
                                                                                          self._attr_state,
                                                                                          self._attr_available))


class MobileAlertsHumiditySensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts humidity sensor. """

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device)
        self._device_class = SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self.entity_description = SensorEntityDescription(
            SensorDeviceClass.HUMIDITY,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
        )

    @property
    def native_value(self) -> StateType:
        return cast(float, self._attr_state)


class MobileAlertsTemperatureSensor(MobileAlertsSensor, CoordinatorEntity, SensorEntity):
    """Implementation of a MobileAlerts humidity sensor. """

    def __init__(self, coordinator, device: dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device=device)
        self._device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self.entity_description = SensorEntityDescription(
            SensorDeviceClass.TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        )

    @property
    def native_value(self) -> StateType:
        return cast(float, self._attr_state)


class MobileAlertsData:
    """
    Get the latest data from MobileAlerts.
    see REST API doc
    https://mobile-alerts.eu/de/home/
    https://mobile-alerts.eu/info/public_server_api_documentation.pdf
    """

    def __init__(self, phone_id: str, devices) -> None:
        self._phone_id = phone_id
        self._data = None
        self._device_ids = []
        for device in devices:
            self.register_device(device[CONF_DEVICE_ID])

    def register_device(self, device_id: str) -> None:
        # _LOGGER.debug("MobileAlertsData::register_device {0}".format(device_id))
        if device_id in self._device_ids:
            return

        self._device_ids.append(device_id)
        _LOGGER.debug("device {0} added - ({1})".format(device_id, self._device_ids))

    def get_reading(self, sensor_id: str) -> Optional[dict]:
        """
        Return current data for the sensor
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
            if sensor_id == sensor_data['deviceid']:
                return sensor_data

        _LOGGER.error("Sensor ID {0} not found".format(sensor_id))
        return None

    async def fetch_data(self) -> None:
        try:
            _LOGGER.debug("MobileAlertsData::fetch_data")
            if len(self._device_ids) == 0:
                _LOGGER.debug("no device ids registered")
                return

            url = 'https://www.data199.com/api/pv1/device/lastmeasurement'
            headers = {
                'Content-Type': 'application/json'
            }
            request_data = {"deviceids": ",".join(self._device_ids)}
            json_data = json.dumps(request_data)
            # todo add phoneid if it's there
            #        if len(self._phone_id) > 0:
            #            data["phoneid"] = self._phone_id

            page_text = ""
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=json_data, headers=headers) as response:
                    page_text = await response.read()
                    if response.status != 200:
                        _LOGGER.error("POST error: {0}, {1}, {2}".format(response.status, url, request_data))

            sensor_response = json.loads(page_text)
            # check data returned has no errors
            if not sensor_response["success"]:
                _LOGGER.warning("Error getting data from MA {0}:{1}".format(sensor_response["errorcode"],
                                                                            sensor_response["errormessage"]))
                self._data = None
                return
            if sensor_response is None:
                _LOGGER.warning("Failed to fetch data from OWM")
                return

            if 'devices' not in sensor_response:
                _LOGGER.warning("MA data contains no devices {0}".format(sensor_response))
                return

            self._data = sensor_response['devices']

        except ConnectionError:
            _LOGGER.warning("Unable to connect to MA URL")
            raise ApiError()
        except TimeoutError:
            _LOGGER.warning("Timeout connecting to MA URL")
            raise ApiError()
        except Exception as e:
            _LOGGER.warning("{0} occurred details: {1}".format(e.__class__, e))
            raise ApiError()
