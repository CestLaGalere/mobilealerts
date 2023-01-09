"""Support for the MobileAlerts service."""
from datetime import timedelta
import logging
import re
from typing import Any, Dict, Tuple, List, Mapping, Optional

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
#from homeassistant.util import Throttle
#, dt

import async_timeout
import aiohttp
from bs4 import BeautifulSoup

import voluptuous as vol
from .mahelper import extract_value_units

SensorAttributes = Dict[str, Any]

from .const import (
    CONF_DEVICES,
    CONF_PHONE_ID,
    ATTRIBUTION,
)

from homeassistant.components.weather import (
    PLATFORM_SCHEMA,
)

from homeassistant.const import (
    CONF_NAME,
    CONF_TYPE,
    CONF_DEVICE_ID,
    ATTR_ATTRIBUTION,
)

from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

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
        vol.Required(CONF_TYPE): vol.All(cv.string, vol.In(SENSOR_READINGS)),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PHONE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [SENSOR_SCHEMA])
        #vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [cv.string])
    }
)




class ApiError(Exception):
    ...
    pass


async def async_setup_platform(
    hass: HomeAssistantType, 
    config: ConfigType, 
    async_add_entities: AddEntitiesCallback, 
    discovery_info: Optional[DiscoveryInfoType] = None,
    ) -> None:
    """Set up the OpenWeatherMap weather platform."""
    session = async_get_clientsession(hass)
    phone_id = config.get(CONF_PHONE_ID)

    mad = MobileAlertsData(phone_id)
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

    async_add_entities(MobileAlertsSensor(coordinator, device) for device in config[CONF_DEVICES])


# see https://developers.home-assistant.io/docs/integration_fetching_data/
class MobileAlertsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, mobile_alerts_data):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self.mobile_alerts_data = mobile_alerts_data


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
                return await self.mobile_alerts_data.fetch_data()
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except:
            _LOGGER.warning('Exception within MobileAlertsCoordinator::_async_update_data')
            raise


    def get_reading(self, sensor_id : str) -> Optional[Dict]:
        return self.mobile_alerts_data.get_reading(sensor_id)


class MobileAlertsData:
    pass


class MobileAlertsSensor(CoordinatorEntity, Entity):
    """Implementation of a MobileAlerts sensor. """

    def __init__(self, coordinator, device: Dict[str, str]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device[CONF_DEVICE_ID]
        self._name = device[CONF_NAME]
        if CONF_TYPE in device:
            self._type = device[CONF_TYPE]
        else:
            self._type = "temperature"
        self._data = None
        self._state = ""
        self._id = self._device_id + self._type[:1]
        
        self._data = self.coordinator.get_reading(self._device_id)
        self._state, self._available = self.extract_reading(self._type, True)

        _LOGGER.debug("MobileAlertsSensor::init ID {0}:{1}".format(self._id, self._state))


    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        #_LOGGER.debug("MobileAlertsSensor::available {0} available:{1}".format(self._name, self._available))
        return self._available

    @property
    def state(self) -> Optional[str]:
        #_LOGGER.debug("MobileAlertsSensor::state {0} available:{1}".format(self._name, self._available))
        return self._state

    @property
    def attribution(self):
        return ATTRIBUTION

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        attrs = {}
        if self._available:
            for name, value in self._data.items():
                #if name.replace(' ','') in SENSOR_READINGS:
                attrs[name] = value
            attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._data = self.coordinator.get_reading(self._device_id)
        self._state, self._available = self.extract_reading(self._type, True)
        _LOGGER.debug("MobileAlertsSensor::_handle_coordinator_update {0} {1}:{2}".format(self._name, self._state, self._available))
        self.async_write_ha_state()


    def extract_reading(self, reading_type : str, remove_units : bool) -> Tuple[str, bool]:
        """
        self._data contains a dictionary build from the scraped web page, e.g.
        {'Name': 'Downstairs', 'timestamp': '12/7/2022 7:04:01 PM', 'temperature': '0.0 C', 'humidity': '92%'}
        """
        if self._data is None:
            return "", False

        if reading_type in self._data:
            value = self._data[reading_type]
            if remove_units:
                value, u = extract_value_units(value)
            return value, True
        
        return "", False


class MobileAlertsData:
    """Get the latest data from MobileAlerts."""

    def __init__(self, phone_id: str) -> None:
        self._phone_id = phone_id
        self._data = None

    def get_reading(self, sensor_id : str) -> Optional[Dict]:
        """
        Return current data for the sensor
        passed:
            sensor_id
        returns:
            dictionary of returned data
            None if the sensor isn't present
        """
        if self._data == None:
            # either still waiting for first call or calls have failed...
            _LOGGER.info("No sensor data")
            return None

        if sensor_id in self._data:
            return self._data[sensor_id]

        _LOGGER.error("Sensor ID {0} not found".format(sensor_id))
        return None


    async def fetch_data(self) -> None:
        try:
            _LOGGER.debug("MobileAlertsData::fetch_data")
            obs = await self.get_current_readings()
            if obs is None:
                _LOGGER.warning("Failed to fetch data from OWM")
                return

            self._data = obs
        except ConnectionError:
            _LOGGER.warning("Unable to connect to MA URL")
            raise ApiError()
        except TimeoutError:
            _LOGGER.warning("Timeout connecting to MA URL")
            raise ApiError()
        except Exception as e:
            _LOGGER.warning("{0} occurred details: {1}".format(e.__class__, e))
            raise ApiError()


    async def get_current_readings(self) -> Dict[str, SensorAttributes]:
        """
        Build dictionary of all panel readings

        Returns
            dictionary of sensors of the form
            { sensor_id1 : {"Name" : "sensor_name, "Timestamp" : "sensor_timestamp", "Reading_name" : "value" }, sensor_id2 : { ... } }
        """
        url = "https://measurements.mobile-alerts.eu"
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        page_text = ""
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data= {"phoneid": self._phone_id}, headers=headers) as response:
                if response.status != 200:
                    raise Exception("requests getting data: {0}, {1}".format(response.status, url))
                page_text = await response.read()

        soup = BeautifulSoup(page_text, "html.parser")
        div_sensors = soup.find_all('div', class_='sensor')

        if len(div_sensors) == 0:
            _LOGGER.warning("No sensors found, check div class name")
            return None

        all_attributes = {}
        for div_sensor in div_sensors:
            sensor_id, attributes = self.extract_panel_reading(div_sensor)
            if len(sensor_id) > 0:
                all_attributes[sensor_id] = attributes
            else:
                _LOGGER.warning("sensor div contains no id")
            #_LOGGER.warning("update {}:{}".format(sensor_id, attributes))

        return all_attributes


    def extract_panel_reading(self, sensor_div) -> Tuple[str, SensorAttributes]:
        """
        Parse the sensor panels and extract the information
        Parameters
            sensor_div - the <div class="sensor"> element - see the html below

        Returns
            Tuple (sensor_id, Dict of attributes)

        input html - see tests \ test_source.html
        """
        attributes = {}
        # name is after the <a> in sensor-header
        sensor_headers = sensor_div.find_all('div', class_='sensor-header')
        sensor_name = sensor_headers[0].h3.a.contents[0]
        attributes["Name"] = sensor_name

        # put all sensor-component names and values into this dictionary
        sensor_components = sensor_div.find_all('div', class_='sensor-component')
        
        sensor_id = ""

        for sensor in sensor_components:
            h5 = sensor.find('h5').contents[0].lower()
            h4 = sensor.find('h4').contents[0]
            if h5 == 'id':
                sensor_id = h4
                continue
            attributes[h5] = h4

        # rain sensor which only contains the name attribute means no rainfall
        if (re.compile(r'\b(rain)\b', flags=re.IGNORECASE).search(sensor_name) is not None
            and len(attributes) == 1):
            attributes["rain"] = "0 mm"

        return sensor_id, attributes