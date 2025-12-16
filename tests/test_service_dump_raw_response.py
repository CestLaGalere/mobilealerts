"""Tests for Mobile Alerts dump_raw_response service."""

import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME

from custom_components.mobile_alerts.const import DOMAIN, CONF_MODEL_ID, CONF_PHONE_ID


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "devices": [
            {
                "deviceid": "090005AC99E2",
                "measurement": {
                    "t1": 21.3,
                    "t2": 11.0,
                    "h": 45.0,
                    "idx": 200,
                    "ts": 1765658719,
                },
            }
        ]
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_123"
    entry.data = {
        CONF_DEVICE_ID: "090005AC99E2",
        CONF_NAME: "Test Device",
        CONF_MODEL_ID: "MA10300",
        CONF_PHONE_ID: "ui_devices",
    }
    entry.title = "Test Device"
    return entry


@pytest.mark.asyncio
async def test_dump_raw_response_service_all_entries(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test dump_raw_response service with no specific entry (dumps all)."""
    # Setup: Initialize domain data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators_by_entry"] = {
        mock_config_entry.entry_id: mock_coordinator
    }

    # Import and register services
    from custom_components.mobile_alerts import _register_services

    await _register_services(hass)

    # Call service without config_entry (should dump all)
    response = await hass.services.async_call(
        DOMAIN,
        "dump_raw_response",
        {},
        blocking=True,
        return_response=True,
    )

    # Verify response
    assert response is not None
    assert response["success"] is True
    assert response["entries_count"] == 1
    assert mock_config_entry.entry_id in response["data"]
    assert response["data"][mock_config_entry.entry_id] == mock_coordinator.data
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_dump_raw_response_service_invalid_entry(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test dump_raw_response service returns all available entries (no entry filtering)."""
    # Setup: Initialize domain data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators_by_entry"] = {
        mock_config_entry.entry_id: mock_coordinator
    }

    # Import and register services
    from custom_components.mobile_alerts import _register_services

    await _register_services(hass)

    # Call service (no parameters)
    response = await hass.services.async_call(
        DOMAIN,
        "dump_raw_response",
        {},
        blocking=True,
        return_response=True,
    )

    # Verify response - should return available entry
    assert response is not None
    assert response["success"] is True
    assert response["entries_count"] == 1


@pytest.mark.asyncio
async def test_dump_raw_response_service_no_entries(hass: HomeAssistant):
    """Test dump_raw_response service when no entries exist."""
    # Setup: Initialize domain data with no entries
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators_by_entry"] = {}

    # Import and register services
    from custom_components.mobile_alerts import _register_services

    await _register_services(hass)

    # Call service with no entries
    response = await hass.services.async_call(
        DOMAIN,
        "dump_raw_response",
        {},
        blocking=True,
        return_response=True,
    )

    # Verify error response
    assert response is not None
    assert response["success"] is False
    assert "No Mobile Alerts entries found" in response["error"]


@pytest.mark.asyncio
async def test_dump_raw_response_service_multiple_entries(hass: HomeAssistant):
    """Test dump_raw_response service with multiple entries."""
    # Setup: Create two mock coordinators
    coordinator1 = MagicMock()
    coordinator1.data = {
        "devices": [{"deviceid": "090005AC99E1", "measurement": {"t1": 20.0}}]
    }
    coordinator1.async_request_refresh = AsyncMock()

    coordinator2 = MagicMock()
    coordinator2.data = {
        "devices": [{"deviceid": "090005AC99E2", "measurement": {"t1": 21.3}}]
    }
    coordinator2.async_request_refresh = AsyncMock()

    entry1_id = "entry_1"
    entry2_id = "entry_2"

    # Setup: Initialize domain data with two entries
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators_by_entry"] = {
        entry1_id: coordinator1,
        entry2_id: coordinator2,
    }

    # Import and register services
    from custom_components.mobile_alerts import _register_services

    await _register_services(hass)

    # Call service without specific entry (should dump all)
    response = await hass.services.async_call(
        DOMAIN,
        "dump_raw_response",
        {},
        blocking=True,
        return_response=True,
    )

    # Verify response includes both entries
    assert response is not None
    assert response["success"] is True
    assert response["entries_count"] == 2
    assert entry1_id in response["data"]
    assert entry2_id in response["data"]
    coordinator1.async_request_refresh.assert_called_once()
    coordinator2.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_dump_raw_response_has_timestamp(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that response includes a valid ISO timestamp."""
    from datetime import datetime

    # Setup
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators_by_entry"] = {
        mock_config_entry.entry_id: mock_coordinator
    }

    from custom_components.mobile_alerts import _register_services

    await _register_services(hass)

    # Call service
    response = await hass.services.async_call(
        DOMAIN,
        "dump_raw_response",
        {},
        blocking=True,
        return_response=True,
    )

    # Verify timestamp
    assert "timestamp" in response
    # Try to parse as ISO format
    parsed = datetime.fromisoformat(response["timestamp"])
    assert parsed is not None
