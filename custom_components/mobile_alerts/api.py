"""Mobile Alerts API communication module."""

import json
import logging
import os
from asyncio import timeout
from typing import Any, Final

import aiohttp

_LOGGER: Final = logging.getLogger(__name__)


class ApiError(Exception):
    """Mobile Alerts API Error."""


class MobileAlertsApi:
    """Interact with Mobile Alerts API."""

    # Allow overriding API URL via environment variable (for testing)
    API_URL = os.getenv(
        "MOBILE_ALERTS_API_URL",
        "https://www.data199.com/api/pv1/device/lastmeasurement",
    )

    def __init__(
        self,
        phone_id: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            phone_id: The Mobile Alerts phone/app id, or the sentinel
                ``"ui_devices"`` for users who configured devices via the HA
                UI without supplying a phone id.
            session: Optional shared ``aiohttp.ClientSession`` (for example from
                ``homeassistant.helpers.aiohttp_client.async_get_clientsession``).
                If omitted, a temporary session is created per request.

        Note:
            The ``phone_id`` is **only** used by :meth:`discover_devices`.
            The ``lastmeasurement`` endpoint deliberately omits it (see
            ``_fetch_device`` / ``_fetch_batch`` below) because the upstream
            API returns ``HTTP 400`` for some accounts when ``phoneid`` is
            included alongside ``deviceids`` (issue #54). The ``phone_id`` is
            still stored on the instance so a future feature (e.g. surfacing
            alert flags per issue #22) can opt back in without re-plumbing
            configuration.
        """
        self._phone_id = phone_id
        self._session = session
        self._device_ids: list[str] = []
        self._data: list[dict[str, Any]] | None = None

    def seed_device_data(self, device_data: dict[str, Any]) -> None:
        """Register a device and seed or update its cached measurement data.

        Updates only the matching device in ``self._data`` so previously cached
        entries for other devices are preserved.

        Args:
            device_data: A single device dictionary from the API response.
        """
        device_id = device_data.get("deviceid")
        if not device_id:
            return

        if device_id not in self._device_ids:
            self._device_ids.append(device_id)
            _LOGGER.debug("Device %s registered via seed", device_id)

        if self._data is None:
            self._data = []

        self._data = [d for d in self._data if d.get("deviceid") != device_id]
        self._data.append(device_data)

    def unregister_device(self, device_id: str) -> None:
        """Remove a device from the polling list and cached data.

        Args:
            device_id: The device ID to unregister.
        """
        if device_id in self._device_ids:
            self._device_ids = [d for d in self._device_ids if d != device_id]
            _LOGGER.debug("Device %s unregistered", device_id)

        if self._data is not None:
            self._data = [d for d in self._data if d.get("deviceid") != device_id]

    async def register_device(self, device_id: str) -> None:
        """Register a device and fetch its data immediately.

        This is called during async_setup_entry to add a new device and fetch
        its data right away. This ensures data is available as soon as the device
        is registered.

        Args:
            device_id: The device ID to register and fetch

        Raises:
            ApiError: If fetching device data fails
        """
        if device_id not in self._device_ids:
            self._device_ids.append(device_id)
            _LOGGER.debug("Device %s registered", device_id)

        # Fetch this device's data immediately
        await self._fetch_device(device_id)

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

    async def fetch_data(self, is_initial: bool = False) -> dict[str, Any] | None:
        """Fetch latest measurement data from Mobile Alerts API.

        For regular 10-minute updates, always uses batch mode to fetch all devices
        in a single request.

        Individual device fetches happen in register_device() during setup.

        Args:
            is_initial: Currently unused - kept for backward compatibility

        Returns:
            dict with API response containing devices data, or None if empty

        Raises:
            ApiError: If API communication fails
        """
        await self._fetch_batch()

        # Return the internal data that was just fetched
        if self._data:
            return {"devices": self._data}
        return None

    async def _fetch_device(self, device_id: str) -> None:
        """Fetch data for a single device during setup.

        Called from register_device() to fetch the newly registered device's data
        without re-fetching all previously registered devices.

        Note:
            We intentionally do **not** send ``phoneid`` with ``lastmeasurement``
            requests. The Mobile Alerts API is inconsistent across accounts:
            when the supplied ``phoneid`` is not linked to the queried
            ``deviceids`` in MA's database the endpoint returns ``HTTP 400``
            (issue #54). The ``phoneid`` is only required by
            :meth:`discover_devices` and is therefore only attached there.

            Side effect: response ``measurement`` payloads will not include
            the alert-flag fields that are gated behind ``phoneid``. The HA
            integration does not currently expose those flags as entities, so
            this is a no-op for users. Re-introducing ``phoneid`` here is a
            future opt-in (issue #22 follow-up) and should be guarded against
            the same ``HTTP 400`` case before being shipped.

        Args:
            device_id: The device ID to fetch

        Raises:
            ApiError: If API communication fails
        """
        _LOGGER.debug("Fetching initial data for device %s", device_id)
        request_payload = {"deviceids": device_id}

        response_data = await self._post_api_request(request_payload)
        if response_data:
            devices = response_data.get("devices", [])
            if devices:
                for device in devices:
                    self.seed_device_data(device)
                _LOGGER.debug("Got initial data for device %s", device_id)
            else:
                _LOGGER.warning("No data returned for device %s", device_id)

    async def _fetch_batch(self) -> None:
        """Fetch all registered devices in a single batch request.

        This is used for regular 10-minute updates to minimize API calls.

        Note:
            Same rationale as :meth:`_fetch_device`: ``phoneid`` is omitted to
            avoid ``HTTP 400`` for accounts where the phoneid is not linked to
            the queried devices in MA's database (issue #54).
        """
        _LOGGER.debug("Fetching data from Mobile Alerts API (batch mode)")

        if not self._device_ids:
            _LOGGER.debug("No devices registered for data fetching")
            return

        request_payload = {"deviceids": ",".join(self._device_ids)}

        response_data = await self._post_api_request(request_payload)
        if response_data:
            devices = response_data.get("devices", [])
            if self._data is None:
                self._data = []
            for device in devices:
                self.seed_device_data(device)
            if devices:
                _LOGGER.debug(
                    "Successfully fetched data for %d devices",
                    len(devices),
                )
                # Log device details for debugging
                for device in devices:
                    device_id = device.get("deviceid", "unknown")
                    measurement = device.get("measurement", {})
                    if measurement:
                        meas_keys = list(measurement.keys())
                        _LOGGER.debug(
                            "Device %s: measurement_keys=%s, data=%s",
                            device_id,
                            meas_keys,
                            measurement,
                        )
            else:
                _LOGGER.warning("No device data returned from API")
        else:
            _LOGGER.error("Failed to fetch data from API")

    def _raise_for_status(self, status: int, body_preview: str = "") -> None:
        """Raise a descriptive ApiError for non-200 HTTP responses."""
        if status == 429:
            _LOGGER.error(
                "Mobile Alerts API rate limit exceeded (HTTP 429): max 3 requests per "
                "sensor per minute; further requests are blocked for 7 minutes (URL: %s)",
                self.API_URL,
            )
            raise ApiError("Rate limit exceeded (HTTP 429): blocked for 7 minutes")
        if status == 403:
            _LOGGER.error(
                "Mobile Alerts API request blocked (HTTP 403): too many invalid "
                "parameters from this IP; blocked for 15 minutes (URL: %s)",
                self.API_URL,
            )
            raise ApiError(
                "Forbidden (HTTP 403): IP temporarily blocked for 15 minutes"
            )
        if body_preview:
            _LOGGER.error(
                "API error: HTTP %s, URL: %s, body: %s",
                status,
                self.API_URL,
                body_preview,
            )
        else:
            _LOGGER.error(
                "API error: HTTP %s, URL: %s",
                status,
                self.API_URL,
            )
        raise ApiError(f"HTTP {status}")

    async def _send_post(
        self, request_payload: dict[str, Any]
    ) -> tuple[int, str]:
        """Send an HTTP POST request using the injected or a temporary session."""
        headers = {"Content-Type": "application/json"}
        json_data = json.dumps(request_payload)

        async with timeout(30):
            if self._session is not None:
                async with self._session.post(
                    self.API_URL, data=json_data, headers=headers
                ) as response:
                    return response.status, await response.text()

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.post(
                    self.API_URL, data=json_data, headers=headers
                ) as response:
                    return response.status, await response.text()

    async def _post_api_request(
        self, request_payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Post a request to the Mobile Alerts API and handle the response.

        This is a private helper method to avoid code duplication between
        single device and batch fetches.

        Args:
            request_payload: The request payload (deviceids and optional phoneid)

        Returns:
            The parsed JSON response, or None if there was an error

        Raises:
            ApiError: If API communication fails
        """
        _LOGGER.debug("API Request: %s", json.dumps(request_payload))

        try:
            status, response_text = await self._send_post(request_payload)
            if status != 200:
                self._raise_for_status(status)

            sensor_response = json.loads(response_text)

            if not sensor_response.get("success", False):
                error_code = sensor_response.get("errorcode")
                error_msg = sensor_response.get("errormessage")
                _LOGGER.error("API error: %s - %s", error_code, error_msg)
                return None

            return sensor_response

        except ApiError:
            raise
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

            _LOGGER.debug("Discovery Request payload: %s", json.dumps(request_payload))

            status, response_text = await self._send_post(request_payload)
            _LOGGER.debug(
                "Discovery API Response: status=%s, body=%s",
                status,
                response_text[:200] if response_text else "empty",
            )

            if status != 200:
                self._raise_for_status(
                    status, response_text[:200] if response_text else ""
                )

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

        except ApiError:
            raise
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
