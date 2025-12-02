"""Config flow for Mobile Alerts integration."""

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigFlowResult

from .api import ApiError, MobileAlertsApi
from .const import CONF_PHONE_ID, CONF_MODEL_ID, DOMAIN
from .device import find_all_matching_models

_LOGGER = logging.getLogger(__name__)


class MobileAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mobile Alerts."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._detected_type: Optional[str] = None
        self._device_data: Optional[dict[str, Any]] = None
        self._device_id: Optional[str] = None
        self._device_name: Optional[str] = None
        self._candidates: list[tuple[str, dict[str, Any]]] = []

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
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
                            all_matches = find_all_matching_models(measurement)

                            if not all_matches:
                                _LOGGER.error(
                                    "Could not detect device model for device %s. "
                                    "Raw measurement data: %s. Device data: %s. "
                                    "Please report this as an issue with the full log output.",
                                    device_id,
                                    measurement,
                                    device_data,
                                )
                                errors["base"] = "device_not_supported"
                            elif len(all_matches) > 1:
                                # Multiple models match - ask user which one
                                _LOGGER.info(
                                    "Device %s ambiguous - multiple models match: %s",
                                    device_id,
                                    [m_id for m_id, _ in all_matches],
                                )
                                # Store data for step2
                                self._device_data = device_data
                                self._device_id = device_id
                                self._device_name = device_name
                                self._candidates = all_matches
                                return await self.async_step_select_model()
                            else:
                                # Single match - proceed normally
                                model_id, model_info = all_matches[0]
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
                    "If you have already configured devices in configuration.yaml "
                    "(older version), they will not be shown in the user interface. "
                    "However, the entities still exist. You can add the Device ID again "
                    "and restart Home Assistant. The devices will then be displayed correctly. "
                    "After that, you can remove the old mobile_alerts entries from "
                    "configuration.yaml."
                ),
            },
        )

    async def async_step_select_model(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle model selection for ambiguous devices.

        Some devices have identical measurement keys but different meanings for keys.
        Example: MA10300 and MA10350 both report {t1, t2, h}
        - MA10300: t2 = cable temperature
        - MA10350: t2 = water level
        """
        if user_input is not None:
            model_id = user_input.get("model_id")

            # Find the selected model info from candidates
            model_info = None
            if self._candidates:
                for cand_id, cand_info in self._candidates:
                    if cand_id == model_id:
                        model_info = cand_info
                        break

            if not model_info:
                _LOGGER.error("Selected model %s not found in candidates", model_id)
                return self.async_abort(reason="device_not_supported")

            device_id = self._device_id
            device_name = self._device_name or ""

            _LOGGER.info(
                "User selected model %s for device %s",
                model_id,
                device_id,
            )

            # Check if this device already exists
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            # Create the entry
            device_title = device_name if device_name else model_info["display_name"]

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
            try:
                _LOGGER.debug(
                    "Seeding coordinator with device data for %s",
                    device_id,
                )
                from .const import DOMAIN

                hass = self.hass
                if DOMAIN in hass.data and "coordinators" in hass.data[DOMAIN]:
                    coordinators = hass.data[DOMAIN]["coordinators"]
                    phone_id = "ui_devices"
                    if phone_id in coordinators:
                        coordinator = coordinators[phone_id]
                        if self._device_data:
                            coordinator.data[device_id] = self._device_data
                            _LOGGER.debug(
                                "Updated coordinator data for device %s",
                                device_id,
                            )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Failed to seed coordinator: %s (non-critical)",
                    err,
                )

            return entry

        # Show model selection form
        if not self._candidates:
            return self.async_abort(reason="device_not_supported")

        # Create human-readable choices from DEVICE_MODELS
        # Format: {model_id: "MA10300 - Wireless Thermo-Hygrometer with Cable Sensor"}
        model_choices = {
            model_id: f"{model_info['name']} - {model_info['display_name']}"
            for model_id, model_info in self._candidates
        }

        return self.async_show_form(
            step_id="select_model",
            data_schema=vol.Schema(
                {
                    vol.Required("model_id"): vol.In(model_choices),
                }
            ),
            description_placeholders={
                "device_id": self._device_id or "unknown",
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
