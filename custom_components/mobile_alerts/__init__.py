"""Mobile Alerts integration."""

import json
import logging
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Service schemas
DUMP_RAW_RESPONSE_SCHEMA = vol.Schema({})


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

    # Register services (only once per integration)
    if DOMAIN not in hass.data or "services_registered" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["services_registered"] = True
        await _register_services(hass)

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
    _LOGGER.debug(
        "Mobile Alerts: async_migrate_entry called, version %s", config_entry.version
    )

    # No migration needed yet
    return True


async def _register_services(hass: HomeAssistant) -> None:
    """Register Mobile Alerts services."""

    async def handle_dump_raw_response(call: ServiceCall) -> dict[str, Any]:
        """Service: Trigger coordinator refresh and return raw API response from all entries.

        Returns data from all Mobile Alerts entries in a single response.
        """
        coordinators_by_entry = hass.data[DOMAIN].get("coordinators_by_entry", {})

        if not coordinators_by_entry:
            return {
                "success": False,
                "error": "No Mobile Alerts entries found",
            }

        # Trigger refresh and collect data from all entries
        results = {}
        for entry_id, coordinator in coordinators_by_entry.items():
            await coordinator.async_request_refresh()
            results[entry_id] = coordinator.data

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "entries_count": len(results),
            "data": results,
        }

    hass.services.async_register(
        DOMAIN,
        "dump_raw_response",
        handle_dump_raw_response,
        schema=DUMP_RAW_RESPONSE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    _LOGGER.debug("Mobile Alerts: Services registered")
