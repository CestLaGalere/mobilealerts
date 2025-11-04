"""Mobile Alerts integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Mobile Alerts component from YAML configuration."""
    _LOGGER.debug("Mobile Alerts: async_setup called - YAML only mode")

    # Initialize domain data
    hass.data.setdefault(DOMAIN, {})

    # Store YAML config if present
    if DOMAIN in config:
        yaml_config = config[DOMAIN]
        hass.data[DOMAIN]["yaml_config"] = yaml_config
        _LOGGER.info("Mobile Alerts: YAML configuration loaded")
    else:
        _LOGGER.debug("Mobile Alerts: No YAML configuration found")

    return True


# CONFIG FLOW FUNCTIONS DEACTIVATED FOR NOW - UNTIL YAML WORKS
# These will be re-enabled in a later step

# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Set up Mobile Alerts from a config entry (ConfigFlow)."""
#     _LOGGER.debug("Config Flow setup entry - DEACTIVATED")
#     return False

# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     _LOGGER.debug("Config Flow unload entry - DEACTIVATED")
#     return False

# async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
#     """Reload config entry."""
#     _LOGGER.debug("Config Flow reload entry - DEACTIVATED")
#     pass

# async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
#     """Migrate an old config entry to a new version."""
#     _LOGGER.debug("Config Flow migrate entry - DEACTIVATED")
#     return False
