"""Test component setup."""

import pytest
from homeassistant.setup import async_setup_component
from custom_components.mobile_alerts.const import DOMAIN

# Stelle sicher, dass das Plugin geladen wird
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.mark.asyncio
async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True
