"""Mobile Alerts API communication module."""

from asyncio import timeout
import json
import logging
from typing import Any, Final

import aiohttp

_LOGGER: Final = logging.getLogger(__name__)


class ApiError(Exception):
    """Mobile Alerts API Error."""


class MobileAlertsApi:
    """Interact with Mobile Alerts API."""

    API_URL = "https://www.data199.com/api/pv1/device/lastmeasurement"

    def __init__(self, phone_id: str) -> None:
        """Initialize the API client."""
        self._phone_id = phone_id
        self._device_ids: list[str] = []
        self._data: list[dict[str, Any]] | None = None

    def register_device(self, device_id: str) -> None:
        """Register a device for data fetching."""
        if device_id not in self._device_ids:
            self._device_ids.append(device_id)
            _LOGGER.debug("Device %s registered", device_id)

    def get_reading(self, device_id: str) -> dict[str, Any] | None:
        """Get sensor reading for a specific device.

        Args:
            device_id: The device ID to fetch data for

        Returns:
            Device data dictionary or None if not found
        """
        if self._data is None:
            _LOGGER.info("No sensor data available yet")
            return None

        for sensor_data in self._data:
            if device_id == sensor_data.get("deviceid"):
                return sensor_data

        _LOGGER.error("Device %s not found in API response", device_id)
        return None

    async def fetch_data(self) -> None:
        """Fetch latest measurement data from Mobile Alerts API.

        Raises:
            ApiError: If API communication fails
        """
        try:
            _LOGGER.debug("Fetching data from Mobile Alerts API")

            if not self._device_ids:
                _LOGGER.debug("No devices registered for data fetching")
                return

            request_payload = {"deviceids": ",".join(self._device_ids)}
            if self._phone_id:
                request_payload["phoneid"] = self._phone_id

            headers = {"Content-Type": "application/json"}
            json_data = json.dumps(request_payload)

            _LOGGER.debug("API Request: %s", json_data)

            async with timeout(30):
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as session:
                    async with session.post(
                        self.API_URL, data=json_data, headers=headers
                    ) as response:
                        if response.status != 200:
                            _LOGGER.error(
                                "API error: HTTP %s, URL: %s",
                                response.status,
                                self.API_URL,
                            )
                            raise ApiError(f"HTTP {response.status}")

                        response_text = await response.text()
                        sensor_response = json.loads(response_text)

                        if not sensor_response.get("success", False):
                            error_code = sensor_response.get("errorcode")
                            error_msg = sensor_response.get("errormessage")
                            _LOGGER.error("API error: %s - %s", error_code, error_msg)
                            self._data = None
                            return

                        if "devices" not in sensor_response:
                            _LOGGER.warning(
                                "API response missing 'devices' key: %s",
                                sensor_response,
                            )
                            self._data = None
                            return

                        self._data = sensor_response.get("devices", [])
                        if self._data:
                            _LOGGER.debug(
                                "Successfully fetched data for %d devices",
                                len(self._data),
                            )

        except TimeoutError as err:
            _LOGGER.warning("Timeout connecting to Mobile Alerts API")
            raise ApiError("Connection timeout") from err
        except aiohttp.ClientError as err:
            _LOGGER.warning("Connection error to Mobile Alerts API: %s", err)
            raise ApiError("Connection error") from err
        except json.JSONDecodeError as err:
            _LOGGER.warning("Invalid JSON response from API: %s", err)
            raise ApiError("Invalid JSON response") from err
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Unexpected error fetching data: %s", err)
            raise ApiError(f"Unexpected error: {err}") from err

    async def discover_devices(self) -> list[dict[str, Any]]:
        """Discover all available devices for this phone_id.

        This is used during setup to find all devices associated with the account.
        Unlike fetch_data(), this doesn't require pre-registered devices.

        Returns:
            List of device dictionaries with 'deviceid' and other fields

        Raises:
            ApiError: If API communication fails
        """
        try:
            _LOGGER.debug(
                "Discovering devices for phone_id %s from Mobile Alerts API",
                self._phone_id,
            )

            # For discovery, send request with phone_id and empty deviceids
            # This tells the API to return all devices for this phone_id
            request_payload = {
                "phoneid": self._phone_id,
                "deviceids": "",  # Empty string to get all devices
            }

            headers = {"Content-Type": "application/json"}
            json_data = json.dumps(request_payload)

            _LOGGER.debug("Discovery Request payload: %s", json_data)

            async with timeout(30):
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as session:
                    async with session.post(
                        self.API_URL, data=json_data, headers=headers
                    ) as response:
                        response_text = await response.text()
                        _LOGGER.debug(
                            "Discovery API Response: status=%s, body=%s",
                            response.status,
                            response_text[:200] if response_text else "empty",
                        )

                        if response.status != 200:
                            _LOGGER.error(
                                "API error: HTTP %s, URL: %s, body: %s",
                                response.status,
                                self.API_URL,
                                response_text[:200],
                            )
                            raise ApiError(f"HTTP {response.status}")

                        sensor_response = json.loads(response_text)

                        if not sensor_response.get("success", False):
                            error_code = sensor_response.get("errorcode")
                            error_msg = sensor_response.get("errormessage")
                            _LOGGER.error("API error: %s - %s", error_code, error_msg)
                            return []

                        devices = sensor_response.get("devices", [])
                        if devices:
                            _LOGGER.debug(
                                "Successfully discovered %d devices",
                                len(devices),
                            )
                        else:
                            _LOGGER.warning(
                                "No devices found for phone_id %s",
                                self._phone_id,
                            )

                        return devices

        except TimeoutError as err:
            _LOGGER.warning("Timeout during device discovery")
            raise ApiError("Connection timeout") from err
        except aiohttp.ClientError as err:
            _LOGGER.warning("Connection error during device discovery: %s", err)
            raise ApiError("Connection error") from err
        except json.JSONDecodeError as err:
            _LOGGER.warning("Invalid JSON response during device discovery: %s", err)
            raise ApiError("Invalid JSON response") from err
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Unexpected error during device discovery: %s", err)
            raise ApiError(f"Unexpected error: {err}") from err
