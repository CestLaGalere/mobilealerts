"""Config flow for Mobile Alerts integration."""

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import ApiError, MobileAlertsApi
from .const import CONF_PHONE_ID, CONF_MODEL_ID, DOMAIN
from .device import detect_device_model

_LOGGER = logging.getLogger(__name__)


class MobileAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mobile Alerts."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._detected_type: Optional[str] = None
        self._device_data: Optional[dict[str, Any]] = None

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - ask for device ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input.get(CONF_DEVICE_ID, "").strip().upper()
            device_name = user_input.get(CONF_NAME, "").strip()

            if not device_id:
                errors["base"] = "invalid_device_id"
            elif len(device_id) != 12:
                errors["base"] = "invalid_device_id_format"
            else:
                # Validate device exists by fetching data from API
                try:
                    # Test API call with empty phone_id (uses public test data)
                    _LOGGER.debug("Validating device %s via API", device_id)
                    api = MobileAlertsApi(phone_id="")
                    # Register device in API (this also fetches its data)
                    await api.register_device(device_id)

                    # Check if device was found in response
                    device_data = api.get_reading(device_id)
                    if device_data is None:
                        _LOGGER.warning(
                            "Device %s not found in API response", device_id
                        )
                        errors["base"] = "device_not_found"
                    else:
                        # Device found! Analyze the response to detect device type
                        _LOGGER.warning(
                            "New device %s found, analyzing sensor types", device_id
                        )

                        measurement = device_data.get("measurement", {})
                        _LOGGER.warning(
                            "New Device %s measurement data: %s",
                            device_id,
                            measurement,
                        )

                        # Check if device has no measurement data (offline/never sent data)
                        if not measurement:
                            last_seen = device_data.get("lastseen")
                            _LOGGER.warning(
                                "Device %s has no measurement data (may be offline). "
                                "Last seen: %s. Device data: %s",
                                device_id,
                                last_seen,
                                device_data,
                            )
                            errors["base"] = "device_offline_no_data"
                        else:
                            # Try to detect the device model from measurement data
                            model_result = detect_device_model(measurement)

                            if not model_result:
                                _LOGGER.error(
                                    "Could not detect device model for device %s. "
                                    "Raw measurement data: %s. Device data: %s. "
                                    "Please report this as an issue with the full log output.",
                                    device_id,
                                    measurement,
                                    device_data,
                                )
                                errors["base"] = "device_not_supported"
                            else:
                                model_id, model_info = model_result
                                _LOGGER.info(
                                    "Device %s identified as %s: %s",
                                    device_id,
                                    model_id,
                                    model_info["display_name"],
                                )

                                # Check if this device already exists
                                await self.async_set_unique_id(device_id)
                                self._abort_if_unique_id_configured()

                                # Store for later use
                                self._device_data = device_data
                                self._detected_type = model_id

                                # Create the config entry with model information
                                device_title = (
                                    device_name
                                    if device_name
                                    else model_info["display_name"]
                                )

                                # Create the entry
                                entry = self.async_create_entry(
                                    title=device_title,
                                    data={
                                        CONF_DEVICE_ID: device_id,
                                        CONF_NAME: device_title,
                                        CONF_MODEL_ID: model_id,
                                        CONF_PHONE_ID: "ui_devices",
                                    },
                                )

                                # Update coordinator with the already-fetched device data
                                # This prevents entities from being "unavailable" and avoids an extra API call
                                # which helps respect the rate limit (max 3 req/min/device)
                                try:
                                    _LOGGER.debug(
                                        "Seeding coordinator with device data for %s",
                                        device_id,
                                    )
                                    from .const import DOMAIN

                                    hass = self.hass
                                    if (
                                        DOMAIN in hass.data
                                        and "coordinators" in hass.data[DOMAIN]
                                    ):
                                        coordinators = hass.data[DOMAIN]["coordinators"]
                                        phone_id = "ui_devices"
                                        if phone_id in coordinators:
                                            coordinator = coordinators[phone_id]
                                            # Directly seed the coordinator with the data we already fetched
                                            # This avoids another API call and respects rate limits
                                            if device_data:
                                                coordinator._api._data = [device_data]
                                                _LOGGER.debug(
                                                    "Coordinator seeded with device data for %s",
                                                    device_id,
                                                )
                                except Exception as err:  # noqa: BLE001
                                    _LOGGER.warning(
                                        "Could not seed coordinator with device data for %s: %s. "
                                        "Data will be available after the next scheduled update.",
                                        device_id,
                                        err,
                                    )

                                return entry

                except ApiError as err:
                    _LOGGER.error("API error validating device %s: %s", device_id, err)
                    errors["base"] = "api_error"
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("Unexpected error validating device: %s", err)
                    errors["base"] = "unknown_error"

        # Show form with info message
        form_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=form_schema,
            errors=errors,
            description_placeholders={
                "migration_info": (
                    "Falls Sie bereits in configuration.yaml Geräte konfiguriert haben "
                    "(ältere Version), werden diese nicht in der Benutzeroberfläche angezeigt. "
                    "Die Entitäten sind jedoch noch vorhanden. Sie können die Geräte-ID erneut "
                    "hinzufügen und Home Assistant neu starten. Die Geräte werden dann korrekt "
                    "angezeigt. Danach können Sie die alten Mobile Alerts Einträge aus "
                    "configuration.yaml entfernen."
                ),
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this config entry."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Mobile Alerts."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:  # type: ignore[override]
        """Manage the options."""
        # For now, no options to manage
        return self.async_abort(reason="not_implemented")
