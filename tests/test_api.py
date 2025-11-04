"""Tests for Mobile Alerts API."""

import pytest

from custom_components.mobile_alerts.api import MobileAlertsApi


@pytest.mark.asyncio
async def test_api_initialization():
    """Test API initialization."""
    api = MobileAlertsApi(phone_id="123456789")
    assert api._phone_id == "123456789"
    assert api._device_ids == []
    assert api._data is None


@pytest.mark.asyncio
async def test_register_device(fake_device_ids):
    """Test device registration."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device(fake_device_ids[0])

    assert fake_device_ids[0] in api._device_ids
    assert len(api._device_ids) == 1


@pytest.mark.asyncio
async def test_register_multiple_devices(fake_device_ids):
    """Test registering multiple devices."""
    api = MobileAlertsApi(phone_id="123456789")

    for device_id in fake_device_ids[:3]:
        api.register_device(device_id)

    assert len(api._device_ids) == 3
    for device_id in fake_device_ids[:3]:
        assert device_id in api._device_ids


@pytest.mark.asyncio
async def test_register_duplicate_device(fake_device_ids):
    """Test that registering the same device twice doesn't duplicate it."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device(fake_device_ids[0])
    api.register_device(fake_device_ids[0])

    assert len(api._device_ids) == 1


@pytest.mark.asyncio
async def test_get_reading_before_fetch(fake_device_ids):
    """Test getting reading before data is fetched."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device(fake_device_ids[0])

    result = api.get_reading(fake_device_ids[0])
    assert result is None


@pytest.mark.asyncio
async def test_get_reading_unregistered_device(fake_device_ids):
    """Test getting reading for unregistered device."""
    api = MobileAlertsApi(phone_id="123456789")

    result = api.get_reading(fake_device_ids[0])
    assert result is None


def test_get_reading_after_data_loaded(fake_device_ids, mock_api_response):
    """Test getting reading after data is loaded."""
    api = MobileAlertsApi(phone_id="123456789")

    # Register devices
    for device_id in fake_device_ids:
        api.register_device(device_id)

    # Manually set data (simulating successful fetch)
    api._data = mock_api_response["devices"]

    # Get reading for first device
    reading = api.get_reading(fake_device_ids[0])
    assert reading is not None
    assert reading["measurement"]["t1"] == 10.0
    assert reading["measurement"]["b"] == 100


def test_get_reading_with_humidity(fake_device_ids, mock_api_response):
    """Test getting reading with humidity measurement."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device(fake_device_ids[1])

    # Set data
    api._data = mock_api_response["devices"]

    reading = api.get_reading(fake_device_ids[1])
    assert reading is not None
    assert reading["measurement"]["t1"] == 19.1
    assert reading["measurement"]["h"] == 61.0
    assert reading["measurement"]["b"] == 95


def test_get_reading_with_multiple_temps(fake_device_ids, mock_api_response):
    """Test getting reading with multiple temperature sensors (t1 and t2)."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device(fake_device_ids[2])

    api._data = mock_api_response["devices"]

    reading = api.get_reading(fake_device_ids[2])
    assert reading is not None
    assert reading["measurement"]["t1"] == 19.6
    assert reading["measurement"]["t2"] == 20.5
    assert reading["measurement"]["b"] == 98


def test_get_reading_nonexistent_device(fake_device_ids, mock_api_response):
    """Test getting reading for device not in API response."""
    api = MobileAlertsApi(phone_id="123456789")
    api.register_device("NONEXISTENT")

    api._data = mock_api_response["devices"]

    reading = api.get_reading("NONEXISTENT")
    assert reading is None
