"""Config flow for Mobile Alerts integration."""

import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import config_validation as cv

from .api import ApiError, MobileAlertsApi
from .const import CONF_DEVICES, CONF_PHONE_ID, DOMAIN, detect_device_type

_LOGGER = logging.getLogger(__name__)


class MobileAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mobile Alerts."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._phone_id: Optional[str] = None
        self._devices: List[Dict[str, Any]] = []
        self._api: Optional[MobileAlertsApi] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Handle the initial step - ask for device ID.

        Each device becomes a separate ConfigEntry.
        """
        errors: Dict[str, str] = {}

        # Check for YAML config exists and redirect to import
        if user_input is None:
            _LOGGER.debug("async_step_user: Checking for YAML configuration")

            # Check for YAML config in hass.data (set by async_setup)
            yaml_config = None
            if DOMAIN in self.hass.data and "yaml_config" in self.hass.data[DOMAIN]:
                yaml_config = self.hass.data[DOMAIN]["yaml_config"]
                _LOGGER.info(
                    "async_step_user: Found YAML config in hass.data: phone_id=%s",
                    yaml_config.get(CONF_PHONE_ID) if yaml_config else None,
                )

            # If YAML config found, redirect to import
            if yaml_config and yaml_config.get(CONF_PHONE_ID):
                _LOGGER.info(
                    "async_step_user: Detected YAML configuration. "
                    "Redirecting to import step..."
                )
                return await self.async_step_import(yaml_config)

            # No YAML, show form to add device manually
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_DEVICE_ID): cv.string,
                        vol.Optional("name"): cv.string,
                    }
                ),
                description_placeholders={
                    "note": "Enter device ID to add a new device. Each device is a separate entry.",
                },
            )

        # User input provided - validate and create entry for this device
        device_id = user_input.get(CONF_DEVICE_ID, "").strip()
        device_name = user_input.get("name", "").strip()

        if not device_id:
            errors["base"] = "invalid_device_id"
        else:
            # Validate device exists
            try:
                api = MobileAlertsApi(phone_id="")
                api.register_device(device_id)

                _LOGGER.debug("Validating device %s via API", device_id)
                await api.fetch_data()

                # Check if device was found in response
                device_data = api.get_reading(device_id)
                if device_data is None:
                    errors["base"] = "device_not_found"
                else:
                    # Device found! Detect its type from measurements
                    device_type = detect_device_type(device_data)

                    # Check if this device already exists
                    for entry in self.hass.config_entries.async_entries(DOMAIN):
                        if entry.data.get(CONF_DEVICE_ID) == device_id:
                            return self.async_abort(reason="device_already_added")

                    # Create entry for this device
                    _LOGGER.info(
                        "Creating ConfigEntry for device %s (type=%s)",
                        device_id,
                        device_type,
                    )

                    return self.async_create_entry(
                        title=device_name
                        if device_name
                        else f"Mobile Alerts {device_id[-4:]}",
                        data={
                            CONF_DEVICE_ID: device_id,
                            "name": device_name
                            if device_name
                            else f"Device {device_id}",
                            "type": device_type,
                            CONF_PHONE_ID: "",
                        },
                    )

            except ApiError as err:
                _LOGGER.error("API error validating device %s: %s", device_id, err)
                errors["base"] = "api_error"
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Unexpected error validating device: %s", err)
                errors["base"] = "unknown_error"

        # Show form again with errors
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Optional("name"): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "note": "Enter device ID to add a new device. Each device is a separate entry.",
            },
        )

    async def async_step_select_devices(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Handle device selection step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            selected_device_ids = user_input.get(CONF_DEVICES, [])

            if not selected_device_ids:
                errors["base"] = "no_devices_selected"
                return self.async_show_form(
                    step_id="select_devices",
                    data_schema=self._get_devices_schema(),
                    errors=errors,
                )

            # Create entry with selected devices
            selected_devices = [
                d for d in self._devices if d["id"] in selected_device_ids
            ]

            return self.async_create_entry(
                title=f"Mobile Alerts ({self._phone_id})",
                data={
                    CONF_PHONE_ID: self._phone_id,
                    CONF_DEVICES: selected_devices,
                },
            )

        return self.async_show_form(
            step_id="select_devices",
            data_schema=self._get_devices_schema(),
        )

    def _get_devices_schema(self) -> vol.Schema:
        """Generate schema for device selection."""
        device_options = {d["id"]: d["name"] for d in self._devices}
        return vol.Schema(
            {
                vol.Required(CONF_DEVICES): vol.All(
                    cv.multi_select(device_options), cv.ensure_list
                )
            }
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this config entry."""
        return OptionsFlowHandler(config_entry)

    async def async_step_import(self, import_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        """Handle import from YAML configuration (migration).

        This step is triggered automatically when YAML config is detected.
        """
        _LOGGER.info("Starting migration from YAML configuration to ConfigEntry")

        phone_id = import_data.get(CONF_PHONE_ID, "").strip()
        devices_config = import_data.get(CONF_DEVICES, [])

        _LOGGER.debug(
            "Import data: phone_id=%s, devices=%d, keys=%s",
            phone_id if phone_id else "(empty)",
            len(devices_config) if devices_config else 0,
            list(import_data.keys()),
        )

        # If we have neither phone_id nor devices, nothing to migrate
        if not phone_id and not devices_config:
            _LOGGER.error("YAML configuration has neither phone_id nor devices")
            return self.async_abort(reason="invalid_yaml")

        # Convert YAML device format to ConfigEntry format
        # OLD YAML: Has multiple entries per device_id with different types (t1, h, t2, etc.)
        # NEW ConfigEntry: Has unique device_ids with type determined from all sensor types

        # First pass: Group sensors by device_id and collect all types
        device_sensor_types: Dict[str, set[str]] = {}
        device_names: Dict[str, str] = {}

        if devices_config:
            for device in devices_config:
                device_id = device.get(CONF_DEVICE_ID)
                if device_id:
                    # Collect all sensor types for this device
                    device_type = device.get("type", "")
                    if device_type:
                        if device_id not in device_sensor_types:
                            device_sensor_types[device_id] = set()
                        device_sensor_types[device_id].add(device_type)

                    # Use first non-empty name for this device
                    if device_id not in device_names:
                        device_names[device_id] = device.get(
                            "name", f"Device {device_id}"
                        )

        # Second pass: Create unique devices based on grouped sensor types
        imported_devices = []

        for device_id, sensor_types in device_sensor_types.items():
            # Determine device type from available sensor types
            # If device has multiple types like {t1, h, t2}, it has temperature + humidity + cable sensor

            # Try to detect device type from combination of sensor types
            detected_type = ""

            # Devices with cable sensor: have both t1 and t2
            if "t1" in sensor_types and "t2" in sensor_types:
                detected_type = "t2"  # Cable sensor type
            # Device with external humidity: has h and h2
            elif "h2" in sensor_types:
                detected_type = "h2"  # External humidity
            # Device with air quality
            elif "ppm" in sensor_types:
                detected_type = "ppm"
            # Device with rain
            elif "r" in sensor_types or "rf" in sensor_types:
                detected_type = "r"
            # Device with wind
            elif any(t in sensor_types for t in ["ws", "wg", "wd"]):
                detected_type = "ws"
            # Device with pressure
            elif "ap" in sensor_types:
                detected_type = "ap"
            # Device with window sensor
            elif "w" in sensor_types:
                detected_type = "w"
            # Device with humidity only
            elif "h" in sensor_types and "t1" not in sensor_types:
                detected_type = "h"
            # Device with temperature only (or temp + humidity)
            elif "t1" in sensor_types:
                if "h" in sensor_types:
                    detected_type = "h"  # Temp + Humidity → use h
                else:
                    detected_type = "t1"

            _LOGGER.debug(
                "Device %s: sensor_types=%s, detected_type=%s",
                device_id,
                sensor_types,
                detected_type,
            )

            imported_devices.append(
                {
                    "id": device_id,
                    "name": device_names.get(device_id, f"Device {device_id}"),
                    "type": detected_type,
                }
            )

        # Check if entry already exists
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            # If we have phone_id, check for duplicate phone_id
            if phone_id and entry.data.get(CONF_PHONE_ID) == phone_id:
                _LOGGER.debug("Config entry for phone_id %s already exists", phone_id)
                return self.async_abort(reason="already_configured")
            # If no phone_id but we have devices, check if those devices already exist
            if not phone_id and imported_devices:
                existing_device_ids = {
                    d.get("id") for d in entry.data.get(CONF_DEVICES, [])
                }
                imported_device_ids = {d.get("id") for d in imported_devices}
                if existing_device_ids & imported_device_ids:  # Intersection
                    _LOGGER.debug("Some devices already configured in existing entry")
                    return self.async_abort(reason="already_configured")

        # If we have phone_id, validate it against API
        if phone_id:
            try:
                _LOGGER.debug(
                    "Validating phone_id %s from YAML",
                    phone_id,
                )
                api = MobileAlertsApi(phone_id=phone_id)
                await api.fetch_data()

                if api._data:
                    _LOGGER.info(
                        "Successfully validated phone_id %s with API",
                        phone_id,
                    )
                else:
                    _LOGGER.warning(
                        "Phone ID %s returned no devices from API.",
                        phone_id,
                    )
            except ApiError as err:
                _LOGGER.error(
                    "Failed to validate phone_id %s with API: %s",
                    phone_id,
                    err,
                )
                return self.async_abort(reason="api_error")
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Unexpected error validating phone_id: %s", err)
                return self.async_abort(reason="unknown_error")

        # Create a separate config entry for EACH device
        # This allows users to enable/disable devices individually
        _LOGGER.info(
            "Successfully migrated from YAML: phone_id=%s, %d device(s)",
            phone_id if phone_id else "(empty)",
            len(imported_devices),
        )

        # Create one ConfigEntry per device
        for device in imported_devices:
            device_id = device.get("id", "")
            device_name = device.get("name", f"Device {device_id}")
            device_type = device.get("type", "")

            # Check if this device already has a config entry
            device_exists = False
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.data.get(CONF_DEVICE_ID) == device_id:
                    device_exists = True
                    _LOGGER.debug("Device %s already configured", device_id)
                    break

            if not device_exists:
                _LOGGER.debug(
                    "Creating ConfigEntry for device: %s (%s, type=%s)",
                    device_id,
                    device_name,
                    device_type,
                )

                # Create entry for this device
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "import", "device_id": device_id},
                        data={
                            CONF_DEVICE_ID: device_id,
                            "name": device_name,
                            "type": device_type,
                            CONF_PHONE_ID: phone_id,
                        },
                    )
                )

        # Schedule YAML removal after entry creation
        async def remove_yaml_config() -> None:
            """Remove YAML config after successful migration."""
            try:
                # Remove YAML config from hass data
                if DOMAIN in self.hass.data:
                    self.hass.data[DOMAIN].pop("yaml_config", None)
                _LOGGER.info(
                    "YAML configuration will be ignored. "
                    "Please remove 'mobile_alerts:' section from configuration.yaml "
                    "to complete the migration."
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Error during YAML cleanup: %s", err)

        # Schedule removal after entries are created
        self.hass.async_create_task(remove_yaml_config())

        # Return successful abort (entries will be created above)
        return self.async_abort(reason="imported_devices")


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Mobile Alerts."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._api: Optional[MobileAlertsApi] = None

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Manage the options - redirect to add device."""
        # Always go to add_device step
        return await self.async_step_add_device()

    async def async_step_add_device(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:  # type: ignore[override]
        """Handle adding a new device via options."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            device_id = user_input.get(CONF_DEVICE_ID, "").strip()
            device_name = user_input.get("name", "").strip()

            if not device_id:
                errors["base"] = "invalid_device_id"
            else:
                # Validate device by fetching data from API
                try:
                    phone_id = self.config_entry.data.get(CONF_PHONE_ID, "")
                    api = MobileAlertsApi(phone_id=phone_id if phone_id else "")
                    api.register_device(device_id)

                    _LOGGER.debug("Validating device %s via API", device_id)
                    await api.fetch_data()

                    # Check if device was found in response
                    device_data = api.get_reading(device_id)
                    if device_data is None:
                        errors["base"] = "device_not_found"
                    else:
                        # Device found! Detect device type from measurement data
                        _LOGGER.info("Device %s validated successfully", device_id)

                        measurement = device_data.get("measurement", {})
                        detected_type = detect_device_type(measurement)

                        _LOGGER.debug(
                            "Detected device type: %s for device %s",
                            detected_type if detected_type else "(unknown)",
                            device_id,
                        )

                        # Get current devices
                        current_devices = self.config_entry.data.get(CONF_DEVICES, [])

                        # Check if device already exists
                        existing_device_ids = [d.get("id") for d in current_devices]
                        if device_id in existing_device_ids:
                            errors["base"] = "device_already_added"
                        else:
                            # Add new device with detected type
                            new_device = {
                                "id": device_id,
                                "name": device_name
                                if device_name
                                else f"Device {device_id}",
                                "type": detected_type,  # Store detected type
                            }
                            updated_devices = current_devices + [new_device]

                            # Update config entry
                            self.hass.config_entries.async_update_entry(
                                self.config_entry,
                                data={
                                    **self.config_entry.data,
                                    CONF_DEVICES: updated_devices,
                                },
                            )

                            _LOGGER.info(
                                "Device %s (type: %s) added to Mobile Alerts config entry",
                                device_id,
                                detected_type if detected_type else "(unknown)",
                            )

                            # Trigger reload to apply changes
                            await self.hass.config_entries.async_reload(
                                self.config_entry.entry_id
                            )

                            return self.async_abort(reason="device_added")

                except ApiError as err:
                    _LOGGER.error("API error validating device %s: %s", device_id, err)
                    errors["base"] = "api_error"
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("Unexpected error validating device: %s", err)
                    errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): cv.string,
                    vol.Optional("name"): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "tip": "The device ID can be found in the Mobile Alerts app"
            },
        )
