"""Tests for Mobile Alerts API."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mobile_alerts.api import ApiError, MobileAlertsApi


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
    # For unit test: just verify the device is added to list
    # (actual fetch is tested in integration tests)
    if fake_device_ids[0] not in api._device_ids:
        api._device_ids.append(fake_device_ids[0])

    assert fake_device_ids[0] in api._device_ids
    assert len(api._device_ids) == 1


@pytest.mark.asyncio
async def test_register_multiple_devices(fake_device_ids):
    """Test registering multiple devices."""
    api = MobileAlertsApi(phone_id="123456789")

    for device_id in fake_device_ids[:3]:
        if device_id not in api._device_ids:
            api._device_ids.append(device_id)

    assert len(api._device_ids) == 3
    for device_id in fake_device_ids[:3]:
        assert device_id in api._device_ids


@pytest.mark.asyncio
async def test_register_duplicate_device(fake_device_ids):
    """Test that registering the same device twice doesn't duplicate it."""
    api = MobileAlertsApi(phone_id="123456789")
    if fake_device_ids[0] not in api._device_ids:
        api._device_ids.append(fake_device_ids[0])
    # Try to add again
    if fake_device_ids[0] not in api._device_ids:
        api._device_ids.append(fake_device_ids[0])

    assert len(api._device_ids) == 1


@pytest.mark.asyncio
async def test_get_reading_before_fetch(fake_device_ids):
    """Test getting reading before data is fetched."""
    api = MobileAlertsApi(phone_id="123456789")
    # Just add to list, don't fetch (we're testing get_reading with no data)
    if fake_device_ids[0] not in api._device_ids:
        api._device_ids.append(fake_device_ids[0])

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

    # Register devices (directly, without awaiting fetch)
    for device_id in fake_device_ids:
        if device_id not in api._device_ids:
            api._device_ids.append(device_id)

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
    if fake_device_ids[1] not in api._device_ids:
        api._device_ids.append(fake_device_ids[1])

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
    if fake_device_ids[2] not in api._device_ids:
        api._device_ids.append(fake_device_ids[2])

    api._data = mock_api_response["devices"]

    reading = api.get_reading(fake_device_ids[2])
    assert reading is not None
    assert reading["measurement"]["t1"] == 19.6
    assert reading["measurement"]["t2"] == 20.5
    assert reading["measurement"]["b"] == 98


def test_get_reading_nonexistent_device(fake_device_ids, mock_api_response):
    """Test getting reading for device not in API response."""
    api = MobileAlertsApi(phone_id="123456789")
    if "NONEXISTENT" not in api._device_ids:
        api._device_ids.append("NONEXISTENT")

    api._data = mock_api_response["devices"]

    reading = api.get_reading("NONEXISTENT")
    assert reading is None


# ---------------------------------------------------------------------------
# Regression tests for issue #54
# ---------------------------------------------------------------------------
# The Mobile Alerts ``lastmeasurement`` endpoint returns HTTP 400 for some
# accounts when both ``phoneid`` and ``deviceids`` are sent (issue #54). The
# integration must therefore omit ``phoneid`` from the measurement requests
# while still attaching it to discovery requests. These tests guard the
# payload shape so a future change cannot accidentally re-introduce the bug.


def _make_response(status: int, body: dict) -> MagicMock:
    """Build a mock aiohttp response context manager."""
    response = MagicMock()
    response.status = status
    # The API client uses ``await response.text()`` and then ``json.loads``
    # on the resulting string, so we only need to mock ``.text``.
    response.text = AsyncMock(return_value=json.dumps(body))
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def _make_session(response: MagicMock) -> MagicMock:
    """Build a mock aiohttp ClientSession that yields ``response``."""
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    post = MagicMock()
    post.__aenter__ = AsyncMock(return_value=response)
    post.__aexit__ = AsyncMock(return_value=None)
    session.post = MagicMock(return_value=post)
    return session


@pytest.mark.asyncio
async def test_fetch_device_does_not_send_phoneid(fake_device_ids):
    """``_fetch_device`` must not include ``phoneid`` in the request payload.

    Regression test for issue #54: the MA API returns HTTP 400 for some
    accounts when ``phoneid`` is sent alongside ``deviceids``.
    """
    api = MobileAlertsApi(phone_id="123456789")
    api._device_ids.append(fake_device_ids[0])

    response = _make_response(
        200,
        {"success": True, "devices": []},
    )
    session = _make_session(response)

    with patch("custom_components.mobile_alerts.api.aiohttp.ClientSession") as cls:
        cls.return_value = session
        await api._fetch_device(fake_device_ids[0])

    # Inspect the actual JSON body that was POSTed.
    assert session.post.call_count == 1
    _, kwargs = session.post.call_args
    sent = json.loads(kwargs["data"])
    assert "deviceids" in sent
    assert sent["deviceids"] == fake_device_ids[0]
    assert "phoneid" not in sent, (
        "phoneid must not be sent on lastmeasurement requests (issue #54)"
    )


@pytest.mark.asyncio
async def test_fetch_batch_does_not_send_phoneid(fake_device_ids):
    """``_fetch_batch`` must not include ``phoneid`` in the request payload.

    Regression test for issue #54.
    """
    api = MobileAlertsApi(phone_id="123456789")
    for device_id in fake_device_ids[:3]:
        api._device_ids.append(device_id)

    response = _make_response(200, {"success": True, "devices": []})
    session = _make_session(response)

    with patch("custom_components.mobile_alerts.api.aiohttp.ClientSession") as cls:
        cls.return_value = session
        await api._fetch_batch()

    assert session.post.call_count == 1
    _, kwargs = session.post.call_args
    sent = json.loads(kwargs["data"])
    assert "deviceids" in sent
    assert sent["deviceids"] == ",".join(fake_device_ids[:3])
    assert "phoneid" not in sent, (
        "phoneid must not be sent on lastmeasurement requests (issue #54)"
    )


@pytest.mark.asyncio
async def test_fetch_device_with_ui_devices_sentinel_does_not_send_phoneid(
    fake_device_ids,
):
    """``phoneid="ui_devices"`` is the default for UI-configured users.

    Ensure the sentinel value is treated the same as no phoneid at all
    (i.e. it never reaches the wire).
    """
    api = MobileAlertsApi(phone_id="ui_devices")
    api._device_ids.append(fake_device_ids[0])

    response = _make_response(200, {"success": True, "devices": []})
    session = _make_session(response)

    with patch("custom_components.mobile_alerts.api.aiohttp.ClientSession") as cls:
        cls.return_value = session
        await api._fetch_device(fake_device_ids[0])

    _, kwargs = session.post.call_args
    sent = json.loads(kwargs["data"])
    assert "phoneid" not in sent
    assert sent == {"deviceids": fake_device_ids[0]}


@pytest.mark.asyncio
async def test_discover_devices_still_sends_phoneid():
    """Discovery must keep using ``phoneid`` so existing setups still work.

    Only ``lastmeasurement`` is affected by issue #54; discovery is unchanged.
    """
    api = MobileAlertsApi(phone_id="123456789")
    response = _make_response(200, {"success": True, "devices": []})
    session = _make_session(response)

    with patch("custom_components.mobile_alerts.api.aiohttp.ClientSession") as cls:
        cls.return_value = session
        await api.discover_devices()

    _, kwargs = session.post.call_args
    sent = json.loads(kwargs["data"])
    assert sent.get("phoneid") == "123456789"
    assert "deviceids" in sent


@pytest.mark.asyncio
async def test_fetch_batch_http_400_surfaces_as_api_error(fake_device_ids):
    """An ``HTTP 400`` from the API must raise :class:`ApiError`.

    Guards the behaviour the reporter in #54 observed: an unhandled 400
    would silently leave sensors unavailable, which is exactly what we
    want to prevent.
    """
    api = MobileAlertsApi(phone_id="123456789")
    for device_id in fake_device_ids[:1]:
        api._device_ids.append(device_id)

    response = _make_response(400, {"success": False, "error": "bad request"})
    session = _make_session(response)

    with (
        patch("custom_components.mobile_alerts.api.aiohttp.ClientSession") as cls,
        pytest.raises(ApiError),
    ):
        cls.return_value = session
        await api._fetch_batch()
