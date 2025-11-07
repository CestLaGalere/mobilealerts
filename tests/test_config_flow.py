"""Tests for Mobile Alerts config flow."""

import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME

from custom_components.mobile_alerts.config_flow import MobileAlertsConfigFlow
from custom_components.mobile_alerts.const import CONF_TYPE

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.mark.asyncio
async def test_config_flow_user_step_invalid_device_id(hass):
    """Test config flow with invalid device ID format."""
    flow = MobileAlertsConfigFlow()
    flow.hass = hass

    user_input = {
        CONF_DEVICE_ID: "123",
        CONF_NAME: "Test Device",
    }

    result = await flow.async_step_user(user_input)

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "errors" in result
    assert result["errors"]["base"] == "invalid_device_id_format"


@pytest.mark.asyncio
async def test_config_flow_user_step_api_error(hass):
    """Test config flow when API call fails."""
    flow = MobileAlertsConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.mobile_alerts.config_flow.MobileAlertsApi"
    ) as mock_api_class:
        from custom_components.mobile_alerts.api import ApiError

        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        # register_device now does the fetch internally
        mock_api.register_device = AsyncMock(side_effect=ApiError("API Error"))

        user_input = {
            CONF_DEVICE_ID: "0B002FA7C3D3",
            CONF_NAME: "Test Device",
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert "errors" in result
        assert result["errors"]["base"] == "api_error"
