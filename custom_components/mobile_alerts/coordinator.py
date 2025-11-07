"""Data update coordinator for Mobile Alerts."""

from datetime import timedelta
import logging
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MobileAlertsApi
from .const import SCAN_INTERVAL_MINUTES

_LOGGER: Final = logging.getLogger(__name__)

# Time between updating data from Mobile Alerts API
SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)


class MobileAlertsCoordinator(DataUpdateCoordinator):
    """Mobile Alerts data update coordinator.

    Fetches data from the Mobile Alerts API and distributes it to all entities
    for a specific phone_id. Multiple devices can be registered with a single
    coordinator, resulting in a single batched API call.
    """

    def __init__(self, hass: HomeAssistant, api: MobileAlertsApi) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Mobile Alerts API instance
        """
        super().__init__(
            hass,
            _LOGGER,
            name="MobileAlertsCoordinator",
            update_interval=SCAN_INTERVAL,
        )
        self._api = api
        self._is_initial_update = True

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Fetch data from API endpoint.

        This method is called at regular intervals (SCAN_INTERVAL) to fetch
        updated data from the Mobile Alerts API. The API batches all registered
        device IDs in a single request.

        On the first update (after setup), devices are fetched individually
        to populate data quickly. On subsequent updates, all devices are
        fetched together in a single batch request.

        Returns:
            dict or None: API response with measurement data for all registered devices

        Raises:
            UpdateFailed: If communication with the API fails
        """
        try:
            _LOGGER.debug(
                "MobileAlertsCoordinator::_async_update_data (is_initial=%s)",
                self._is_initial_update,
            )
            result = await self._api.fetch_data(is_initial=self._is_initial_update)
            # After first update, switch to batch mode
            if self._is_initial_update:
                self._is_initial_update = False
            return result
        except Exception as err:
            raise UpdateFailed("Error communicating with API") from err

    def get_reading(self, sensor_id: str) -> dict[str, Any] | None:
        """Extract sensor reading from coordinator data.

        Args:
            sensor_id: The device ID to retrieve data for

        Returns:
            dict or None: Measurement data for the sensor, or None if not available
        """
        return self._api.get_reading(sensor_id)
