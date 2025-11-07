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
    _LOGGER.debug("Mobile Alerts: async_setup called")

    # Initialize domain data
    hass.data.setdefault(DOMAIN, {})

    # Store YAML config if present
    if DOMAIN in config:
        yaml_config = config[DOMAIN]
        hass.data[DOMAIN]["yaml_config"] = yaml_config
        _LOGGER.info(
            "Mobile Alerts: YAML configuration found. "
            "Please use the UI to configure devices manually or wait for migration feature."
        )
    else:
        _LOGGER.debug("Mobile Alerts: No YAML configuration found")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mobile Alerts from a config entry."""
    _LOGGER.debug("Mobile Alerts: async_setup_entry called for %s", entry.entry_id)
    
    # Initialize domain data if needed
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("entries", {})
    
    # Store entry data
    hass.data[DOMAIN]["entries"][entry.entry_id] = entry
    
    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listen for config entry updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Mobile Alerts: async_unload_entry called for %s", entry.entry_id)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Mobile Alerts: async_reload_entry called for %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate an old config entry to a new version."""
    _LOGGER.debug("Mobile Alerts: async_migrate_entry called, version %s", config_entry.version)
    
    # No migration needed yet
    return True



