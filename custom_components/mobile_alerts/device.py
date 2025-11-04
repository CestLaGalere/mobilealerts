"""Mobile Alerts device management."""

import logging
from typing import Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceInfo

from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


class MobileAlertsDevice:
    """Represents a Mobile Alerts device."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        name: str,
        phone_id: str | None = None,
    ) -> None:
        """Initialize device."""
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.phone_id = phone_id

    @property
    def unique_id(self) -> str:
        """Return unique identifier for this device."""
        return f"{DOMAIN}_{self.device_id}"

    def get_device_info(self) -> DeviceInfo:
        """Return device info for Home Assistant device registry."""
        identifiers = {(DOMAIN, self.device_id)}

        return DeviceInfo(
            identifiers=identifiers,
            name=self.name,
            manufacturer="Mobile Alerts",
            model=self.device_type,
            via_device=None,
        )


class MobileAlertsDeviceManager:
    """Manage Mobile Alerts devices in Home Assistant."""

    def __init__(self, hass: HomeAssistant, device_registry: DeviceRegistry) -> None:
        """Initialize device manager."""
        self._hass = hass
        self._device_registry = device_registry
        self._devices: dict[str, MobileAlertsDevice] = {}

    def add_device(
        self,
        device_id: str,
        device_type: str,
        name: str,
        phone_id: str | None = None,
    ) -> MobileAlertsDevice:
        """Add or update a device."""
        device = MobileAlertsDevice(
            device_id=device_id,
            device_type=device_type,
            name=name,
            phone_id=phone_id,
        )

        # Register device in Home Assistant device registry
        self._device_registry.async_get_or_create(
            config_entry_id=None,
            identifiers={
                (DOMAIN, device_id),
            },
            name=name,
            manufacturer="Mobile Alerts",
            model=device_type,
        )

        self._devices[device_id] = device
        _LOGGER.debug("Device added: %s (%s)", name, device_id)

        return device

    def get_device(self, device_id: str) -> MobileAlertsDevice | None:
        """Get device by ID."""
        return self._devices.get(device_id)

    def get_all_devices(self) -> list[MobileAlertsDevice]:
        """Get all registered devices."""
        return list(self._devices.values())

    def remove_device(self, device_id: str) -> None:
        """Remove a device."""
        if device_id in self._devices:
            del self._devices[device_id]
            _LOGGER.debug("Device removed: %s", device_id)
