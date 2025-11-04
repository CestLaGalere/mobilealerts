"""Pytest configuration and fixtures for Mobile Alerts integration tests."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

# Fake device IDs and phone_id for testing
FAKE_PHONE_ID = "582614729539"

FAKE_DEVICE_IDS = [
    "A1B2C3D4E5F6",
    "B2C3D4E5F6A7",
    "C3D4E5F6A7B8",
    "D4E5F6A7B8C9",
    "E5F6A7B8C9D0",
    "F6A7B8C9D0E1",
    "A7B8C9D0E1F2",
    "B8C9D0E1F2A3",
]

# Mock API response data
# Devices include various sensor types from the API documentation
MOCK_API_RESPONSE = {
    "devices": [
        # ID02/ID20: Simple Temperature sensor (t1 only)
        {
            "deviceid": FAKE_DEVICE_IDS[0],
            "lastseen": 1761498841,
            "lowbattery": False,
            "measurement": {
                "idx": 145252,
                "ts": 1761498838,
                "c": 1761498841,
                "b": 100,
                "t1": 10.0,
            },
        },
        # ID03/ID0E: Thermo/Hygrometer (t1, h)
        {
            "deviceid": FAKE_DEVICE_IDS[1],
            "lastseen": 1761498849,
            "lowbattery": False,
            "measurement": {
                "idx": 143866,
                "ts": 1761498841,
                "c": 1761498849,
                "b": 95,
                "t1": 19.1,
                "h": 61.0,
            },
        },
        # ID01/ID04: Thermometer with cable sensor (t1, t2)
        {
            "deviceid": FAKE_DEVICE_IDS[2],
            "lastseen": 1761498824,
            "lowbattery": False,
            "measurement": {
                "idx": 81756,
                "ts": 1761498818,
                "c": 1761498824,
                "b": 98,
                "t1": 19.6,
                "t2": 20.5,
            },
        },
        # ID06/ID09: Thermo/Hygrometer with cable sensor (t1, t2, h)
        {
            "deviceid": FAKE_DEVICE_IDS[3],
            "lastseen": 1761498794,
            "lowbattery": False,
            "measurement": {
                "idx": 54194,
                "ts": 1761498784,
                "c": 1761498794,
                "b": 92,
                "t1": 19.7,
                "t2": 21.0,
                "h": 55.0,
            },
        },
        # ID05: Thermo/Hygrometer with air quality (t1, t2, h, ppm)
        {
            "deviceid": FAKE_DEVICE_IDS[4],
            "lastseen": 1761498363,
            "lowbattery": False,
            "measurement": {
                "idx": 143659,
                "ts": 1761498359,
                "c": 1761498363,
                "b": 87,
                "t1": 20.4,
                "h": 53.0,
                "ppm": 750.0,
            },
        },
        # ID07: Dual Thermo/Hygrometer (t1, t2, h, h2)
        {
            "deviceid": FAKE_DEVICE_IDS[5],
            "lastseen": 1761498659,
            "lowbattery": False,
            "measurement": {
                "idx": 143759,
                "ts": 1761498656,
                "c": 1761498659,
                "b": 88,
                "t1": 19.3,
                "t2": 18.5,
                "h": 61.0,
                "h2": 58.5,
            },
        },
        # ID08: Rain gauge (t1, r, rf)
        {
            "deviceid": FAKE_DEVICE_IDS[6],
            "lastseen": 1761498795,
            "lowbattery": False,
            "measurement": {
                "idx": 143957,
                "ts": 1761498791,
                "c": 1761498795,
                "b": 91,
                "t1": 20.2,
                "r": 11.352,
                "rf": 44,
            },
        },
        # ID18: Thermo/Hygrometer/Barometer (t1, h, ap)
        {
            "deviceid": FAKE_DEVICE_IDS[7],
            "lastseen": 1761498651,
            "lowbattery": False,
            "measurement": {
                "idx": 3699,
                "ts": 1761498646,
                "c": 1761498651,
                "b": 89,
                "t1": 17.6,
                "h": 54.0,
                "ap": 1019.8,
            },
        },
    ],
    "success": True,
}

# Configuration for the old YAML format
FAKE_CONFIG_YAML = {
    "platform": "mobile_alerts",
    "phone_id": FAKE_PHONE_ID,
    "devices": [
        {
            "device_id": FAKE_DEVICE_IDS[0],
            "name": "Pflanzenhaus Temperatur",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[1],
            "name": "Kinderzimmer OG Süd Temp",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[1],
            "name": "Kinderzimmer OG Süd Feuchte",
            "type": "h",
        },
        {
            "device_id": FAKE_DEVICE_IDS[2],
            "name": "Heizung Vorlauf Temp Raum",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[2],
            "name": "Heizung Vorlauf Temp Leitung",
            "type": "t2",
        },
        {
            "device_id": FAKE_DEVICE_IDS[3],
            "name": "Heizung Rücklauf Temp Raum",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[3],
            "name": "Heizung Rücklauf Temp Leitung",
            "type": "t2",
        },
        {
            "device_id": FAKE_DEVICE_IDS[4],
            "name": "Wohnzimmer EG Temp",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[4],
            "name": "Wohnzimmer EG Feuchte",
            "type": "h",
        },
        {
            "device_id": FAKE_DEVICE_IDS[5],
            "name": "Kinderzimmer OG Nord Temp",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[5],
            "name": "Kinderzimmer OG Nord Feuchte",
            "type": "h",
        },
        {
            "device_id": FAKE_DEVICE_IDS[6],
            "name": "Schlafzimmer EG Temp",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[6],
            "name": "Schlafzimmer EG Feuchte",
            "type": "h",
        },
        {
            "device_id": FAKE_DEVICE_IDS[7],
            "name": "Schutzraum Temp",
            "type": "t",
        },
        {
            "device_id": FAKE_DEVICE_IDS[7],
            "name": "Schutzraum Feuchte",
            "type": "h",
        },
    ],
}


@pytest.fixture
def mock_api_response():
    """Return mock API response data."""
    return json.loads(json.dumps(MOCK_API_RESPONSE))


@pytest.fixture
def fake_phone_id():
    """Return fake phone ID for testing."""
    return FAKE_PHONE_ID


@pytest.fixture
def fake_device_ids():
    """Return fake device IDs for testing."""
    return FAKE_DEVICE_IDS


@pytest.fixture
def fake_config():
    """Return fake configuration (old YAML format)."""
    return json.loads(json.dumps(FAKE_CONFIG_YAML))


@pytest.fixture
def mock_aiohttp_client(aiohttp_client):
    """Mock aiohttp client that returns fake API responses."""

    async def mock_get(url, params=None):
        """Mock GET request to Mobile Alerts API."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=json.dumps(MOCK_API_RESPONSE))
        mock_response.json = AsyncMock(return_value=MOCK_API_RESPONSE)
        return mock_response

    return mock_get


@pytest.fixture
def mock_api_client():
    """Mock the Mobile Alerts API client."""
    mock_client = AsyncMock()
    mock_client.fetch_data = AsyncMock()
    mock_client.get_reading = MagicMock(
        side_effect=lambda device_id: next(
            (
                device["measurement"]
                for device in MOCK_API_RESPONSE["devices"]
                if device["deviceid"] == device_id
            ),
            None,
        )
    )
    return mock_client
