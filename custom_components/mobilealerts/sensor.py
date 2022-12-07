"""Support for the MobileAlerts service."""
from datetime import timedelta
import logging
import re
from typing import Any, Dict, Tuple, List, Mapping, Optional



from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import homeassistant.helpers.config_validation as cv
#from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
#, dt

import requests
from bs4 import BeautifulSoup

import voluptuous as vol
from .mahelper import extract_value_units

from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_PHONE_ID,
)

from homeassistant.components.weather import (
    PLATFORM_SCHEMA,
    WeatherEntity,
)

from homeassistant.const import (
    CONF_NAME,
    CONF_DEVICE_ID,
    TEMP_CELSIUS,
    ATTR_ATTRIBUTION
)

from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

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




_LOGGER = logging.getLogger(__name__)

# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=10)

ATTRIBUTION = "Data provided by MobileAlerts"

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_NAME, default=""): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PHONE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [SENSOR_SCHEMA])
        #vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [cv.string])
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)

    session = async_get_clientsession(hass)

    phone_id = config.get(CONF_PHONE_ID)
    mad = MobileAlertsData(phone_id)

    sensors = [MobileAlertsSensor(device, mad) for device in config[CONF_DEVICES]]
    async_add_entities(sensors, update_before_add=True)


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

    sensors = [MobileAlertsSensor(device, mad) for device in config[CONF_DEVICES]]
    async_add_entities(sensors, update_before_add=True)


class MobileAlertsData:
    pass

class MobileAlertsSensor(Entity):
    """Implementation of an MobileAlerts sensor. """

    def __init__(self, device:  Dict[str, str], mad: MobileAlertsData) -> None:
        """Initialize the sensor."""
        self._device_id = device[CONF_DEVICE_ID]
        self._name = CONF_NAME
        self._mad = mad
        self._data = None
        self._condition = ""

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def state(self) -> Optional[str]:
        return self._condition

    @property
    def temperature(self):
        return self.extract_reading("temperature", True)

    @property
    def temperature_unit(self) -> str:
        return TEMP_CELSIUS

    @property
    def pressure(self):
        return self.extract_reading("pressure", True)

    @property
    def humidity(self):
        hum = self.extract_reading("humidity", True)
        if hum == "":
            hum = 0
        return hum

    @property
    def wind_speed(self):
        return self.extract_reading("windspeed", True)

    @property
    def wind_bearing(self) -> str:
        return self.extract_reading("wind direction", True)

    @property
    def attribution(self):
        return ATTRIBUTION

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        data = {}
        for name, value in self._data.items():
            #if name.replace(' ','') in SENSOR_READINGS:
            data[name] = value
        data[ATTR_ATTRIBUTION] = ATTRIBUTION
        return data


    def extract_reading(self, reading_type : str, remove_units : bool) -> str:
        if self._data is None:
            return ""
        # self._data
        # {'Name': 'Downstairs', 'timestamp': '12/7/2022 7:04:01 PM', 'temperature': '0.0 C', 'humidity': '92%'}

        if reading_type in self._data:
            value = self._data[reading_type]
            if remove_units:
                value, u = extract_value_units(value)
            return value
        
        return ""


    def update(self) -> None:
        """Get the latest data from Mobile Alerts """
        try:
            self._mad.update()
        except:
            _LOGGER.error("Exception when calling MA web API to update data")
            return

        self._data = self._mad.get_reading(self._device_id)

        self._condition = self.extract_reading("temperature", True)
        # + ", " + self.extract_reading("wind direction", False) + ", " + self.extract_reading("windspeed", False)


class MobileAlertsData:
    """Get the latest data from MobileAlerts."""

    def __init__(self, phone_id) -> None:
        self._phone_id = phone_id
        self._data = None


    def get_reading(self, sensor_id : cv.string):
        if self._data == None:
            _LOGGER.error("Sensor ID {0} not found".format(sensor_id))
            return None

        if sensor_id in self._data:
            return self._data[sensor_id]

        _LOGGER.error("Sensor ID {0} not found".format(sensor_id))
        return None


    @Throttle(SCAN_INTERVAL)
    def update(self) -> None:
        try:
            obs = self.get_current_readings()
            if obs is None:
                _LOGGER.warning("Failed to fetch data from OWM")
                return

            self._data = obs
        except ConnectionError:
            _LOGGER.warning("Unable to connect to MA URL")
        except TimeoutError:
            _LOGGER.warning("Timeout connecting to MA URL")
        except Exception as e:
            _LOGGER.warning("{0} occurred details: {1}".format(e.__class__, e))


    def get_current_readings(self):
        """
        Build dictionary of all panel readings
        """
        url = "https://measurements.mobile-alerts.eu"
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.post(url, data= {"phoneid": self._phone_id}, headers=headers)
        if response.status_code != requests.codes.ok:
            raise Exception("requests getting data: {0}, {1}".format(response.status_code, url))
        page_text = response.text

        soup = BeautifulSoup(page_text, "html.parser")
        div_sensors = soup.find_all('div', class_='sensor')

        if len(div_sensors) == 0:
            _LOGGER.warning("No sensors found, check div class name")
            return None

        all_attributes = {}
        for div_sensor in div_sensors:
            sensor_id, attributes = self.extract_panel_reading(div_sensor)
            #_LOGGER.warning("update {}:{}".format(sensor_id, attributes))
            all_attributes[sensor_id] = attributes

        return all_attributes


    def extract_panel_reading(self, sensor_div):
        """
        Parse the sensor panels and extract the information
        Parameters
            sensor_div - the <div class="sensor"> element - see the html below

        Returns
            dictionary of sensors of the form
            { sensor_id : {"Name" : "sensor_name, "Timestamp" : "sensor_timestamp", "Reading_name" : "value" }, sensor_id2 : { ... } }

        html looks as follows:
        <div class="panel panel-default">
            <div class="panel-body">
                <div class="sensor">

                    <div class="sensor-header">
                        <h3>
                            <a
                                href="/Home/MeasurementDetails?deviceid=XXXXXXXXXXXX&amp;vendorid=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&amp;appbundle=eu.mobile_alerts.mobilealerts">Panel Name</a>
                        </h3>
                        <div class="sensor-component">
                            <h5>ID</h5>
                            <h4>XXXXXXXXXXXX</h4>
                        </div>
                    </div>

                    <div class="nofloat"></div>

                    <div class="sensor-component">
                        <h5>Timestamp</h5>
                        <h4>6/9/2020 9:14:18 AM</h4>
                    </div>
                    <div class="sensor-component">
                        <h5>Temperature</h5>
                        <h4>12.9 C</h4>
                    </div>
                    <div class="sensor-component">
                        <h5>Humidity</h5> <!-- Luftfeuchtigkeit -->
                        <h4>93%</h4>
                    </div>
                </div>
            </div>
        </div>
        """
        attributes = {}
        # name is after the <a> in sensor-header
        sensor_headers = sensor_div.find_all('div', class_='sensor-header')
        sensor_name = sensor_headers[0].h3.a.contents[0]
        attributes["Name"] = sensor_name

        # put all sensor-component names and values into this dictionary
        sensor_components = sensor_div.find_all('div', class_='sensor-component')
        
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