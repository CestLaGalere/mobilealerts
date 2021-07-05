"""Support for the MobileAlerts service."""
from datetime import timedelta
import logging
import re

import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    PLATFORM_SCHEMA,
    WeatherEntity,
)

from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
    CONF_DEVICE_ID,
    PRESSURE_HPA,
    PRESSURE_INHG,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    ATTR_ATTRIBUTION
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

import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.util.pressure import convert as convert_pressure

import requests
from bs4 import BeautifulSoup

from . import extract_start_stop, extract_value_units

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by MobileAlerts"

DEFAULT_NAME = "MobileAlerts"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

# other consts
PHONE_ID = "phone_id"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(PHONE_ID): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_ID, default=[]): vol.All(cv.ensure_list, [cv.string])
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the OpenWeatherMap weather platform."""

    name = config.get(CONF_NAME)
    phone_id = config.get(PHONE_ID)

    device_ids = []
    for device_id in config[CONF_DEVICE_ID]:
        device_ids.append(device_id)

    mad = MobileAlertsData(phone_id, device_ids)
    async_add_entities(
        [MobileAlertsWeather(name, mad)],
        True,
    )


class MobileAlertsWeather(WeatherEntity):
    """Implementation of an MobileAlerts sensor. """

    def __init__(self, name, mad):
        """Initialize the sensor."""
        self._name = name
        self._mad = mad
        self.data = None

    @property
    def name(self):
        return self._name

    @property
    def condition(self):
        return self._condition

    @property
    def temperature(self):
        return self.extract_reading("temperature", True)

    @property
    def temperature_unit(self):
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
    def wind_bearing(self):
        return self.extract_reading("wind direction", True)

    @property
    def attribution(self):
        return ATTRIBUTION

    @property
    def state_attributes(self):
        data = {}
        for sensor_id, sensor_parameters in self.data.items():
            for name, value in sensor_parameters.items():
                if name.replace(' ','') in SENSOR_READINGS:
                    data[name] = value
        data[ATTR_ATTRIBUTION] = ATTRIBUTION
        return data


    def extract_reading(self, reading_type, remove_units):
        if self.data is None:
            return ""

        for sensor_id, sensor_parameters in self.data.items():
            for name, value in sensor_parameters.items():
                if name == reading_type:
                    if remove_units:
                        value, u = extract_value_units(value)
                    return value
        
        return ""


    def update(self):
        """Get the latest data from Mobile Alerts and updates the states."""
        try:
            self._mad.update()
        except:
            _LOGGER.error("Exception when calling MA web API to update data")
            return

        self.data = self._mad.data
        self._condition = self.extract_reading("temperature", False) + ", " + self.extract_reading("wind direction", False) + ", " + self.extract_reading("windspeed", False)


class MobileAlertsData:
    """Get the latest data from MobileAlerts."""

    def __init__(self, phone_id, device_ids):
        self._phone_id = phone_id
        self._device_ids = device_ids
        self.data = None


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):

        try:
            obs = self.get_current_readings(self._phone_id, self._device_ids)
            if obs is None:
                _LOGGER.warning("Failed to fetch data from OWM")
                return

            self.data = obs
        except ConnectionError:
            _LOGGER.warning("Unable to connect to MA URL")
        except TimeoutError:
            _LOGGER.warning("Timeout connecting to MA URL")
        except Exception as e:
            _LOGGER.warning("{0} occurred details: {1}".format(e.__class__, e))


    def get_current_readings(self, phone_id, device_ids):
        url = "https://measurements.mobile-alerts.eu"
        response = requests.post(url, data= {"phoneid": phone_id})
        if response.status_code != requests.codes.ok:
            raise Exception("requests getting data: {0}, {1}".format(response.status_code, url))
        page_text = response.text

        soup = BeautifulSoup(page_text, "html.parser")
        div_sensors = soup.find_all('div', class_='sensor')

        if len(div_sensors) == 0:
            _LOGGER.warning("No sensors found, check div class name")
            _LOGGER.warning(page_text)
            return None

        all_attributes = {}
        for div_sensor in div_sensors:
            sensor_id, attributes = self.extract_panel_reading(div_sensor)
            #_LOGGER.warning("update {}:{}".format(sensor_id, attributes))
            if len(device_ids) == 0 or sensor_id in device_ids:
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