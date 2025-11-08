#!/usr/bin/env python3
"""Mock Mobile Alerts API Server for testing.

This server simulates the Mobile Alerts API to allow testing of the Home Assistant
integration without requiring real devices or API calls.

Usage:
    python3 tests/mock_api_server.py [--port 8888]

Environment Variables:
    MOCK_API_PORT: Port to run the server on (default: 8888)

The server provides several test devices:
- MA10100: Wireless Thermometer (only t1)
- MA10200: Wireless Thermo-Hygrometer (t1, h)
- MA10230: Wireless Room Climate Station (t1, h, h3havg, h24havg, h7davg, h30davg)
- MA10300: Wireless Thermo-Hygrometer with Cable Sensor (t1, t2=cable_temp, h)
- MA10350: Wireless Thermo-Hygrometer with Water Detector (t1, t2=water_level, h)
- MA10800: Wireless Window/Door Contact (w=boolean)
- MA10880: Wireless Switch (kp1t, kp1c)

Test Device IDs:
- 090005AC99E1: MA10100
- 090005AC99E2: MA10200
- 090005AC99E3: MA10230
- 107EEEB46F00: MA10300 (cable temperature)
- 107EEEB46F02: MA10350 (water level) ← Ambiguous with MA10300
- 1200099803A1: MA10800 (window contact)
- 1200099803A2: MA10880 (wireless switch)
"""

import argparse
import asyncio
import copy
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Any, Dict, List

from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
_LOGGER = logging.getLogger(__name__)

# Test device definitions
TEST_DEVICES: Dict[str, Dict[str, Any]] = {
    "090005AC99E1": {
        "name": "MA10100 - Thermometer",
        "model": "MA10100",
        "measurement": {
            "idx": 100,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "t1": 22.5,
        },
    },
    "090005AC99E2": {
        "name": "MA10200 - Thermo-Hygrometer",
        "model": "MA10200",
        "measurement": {
            "idx": 200,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "t1": 21.3,
            "h": 45.0,
        },
    },
    "090005AC99E3": {
        "name": "MA10230 - Room Climate Station",
        "model": "MA10230",
        "measurement": {
            "idx": 230,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "t1": 20.8,
            "h": 48.0,
            "h3havg": 47.5,
            "h24havg": 46.2,
            "h7davg": 45.8,
            "h30davg": 44.5,
        },
    },
    "107EEEB46F00": {
        "name": "MA10300 - Thermo-Hygrometer with Cable Sensor",
        "model": "MA10300",
        "measurement": {
            "idx": 300,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "t1": 19.7,  # Internal temperature
            "t2": 18.2,  # Cable temperature (NOT water!)
            "h": 42.0,
        },
    },
    "107EEEB46F02": {
        "name": "MA10350 - Thermo-Hygrometer with Water Detector",
        "model": "MA10350",
        "measurement": {
            "idx": 350,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "t1": 22.1,  # Internal temperature
            "t2": 1,  # Water level (0=no water, 1=water detected) - SAME KEY as MA10300!
            "h": 38.5,
        },
    },
    "1200099803A1": {
        "name": "MA10800 - Window/Door Contact",
        "model": "MA10800",
        "measurement": {
            "idx": 800,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "w": False,  # Window closed
            "wsct": True,  # Window sensor connected
            "wutt": True,  # Battery ok
        },
    },
    "1200099803A2": {
        "name": "MA10880 - Wireless Switch",
        "model": "MA10880",
        "measurement": {
            "idx": 880,
            "ts": int(datetime.now().timestamp()),
            "c": int(datetime.now().timestamp()) + 5,
            "kp1t": 1,  # Key press 1 type
            "kp1c": 42,  # Key press 1 counter
            "kp2t": 2,  # Key press 2 type
            "kp2c": 15,  # Key press 2 counter
            "kp3t": 3,  # Key press 3 type
            "kp3c": 8,  # Key press 3 counter
            "kp4t": 4,  # Key press 4 type
            "kp4c": 23,  # Key press 4 counter
        },
    },
}


class MockAPIServer:
    """Mock Mobile Alerts API Server."""

    def __init__(self, port: int = 8888):
        """Initialize the mock API server."""
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup API routes."""
        self.app.router.add_post("/api/pv1/device/lastmeasurement", self.handle_api)
        self.app.router.add_post("/api/pv1/device/register", self.handle_register)
        self.app.router.add_get("/health", self.handle_health)

    async def handle_api(self, request: web.Request) -> web.Response:
        """Handle lastmeasurement API calls."""
        try:
            data = await request.json()
            device_ids = data.get("deviceids", "").split(",")

            devices = []
            for device_id in device_ids:
                device_id = device_id.strip().upper()
                if device_id in TEST_DEVICES:
                    # Make a deep copy to avoid modifying the original test data
                    device_data = copy.deepcopy(TEST_DEVICES[device_id])
                    device_data["id"] = device_id
                    device_data["deviceid"] = device_id
                    # Update timestamp to current time
                    device_data["measurement"]["ts"] = int(datetime.now().timestamp())
                    device_data["measurement"]["c"] = (
                        int(datetime.now().timestamp()) + 5
                    )
                    devices.append(device_data)
                    _LOGGER.info(
                        "API: Returning data for device %s (%s)",
                        device_id,
                        device_data.get("name", "Unknown"),
                    )
                else:
                    _LOGGER.warning("API: Device %s not found", device_id)

            response = {"success": True, "devices": devices}
            _LOGGER.debug("API Response: %s", json.dumps(response, indent=2))
            return web.json_response(response)

        except Exception as err:
            _LOGGER.error("API Error: %s", err)
            return web.json_response({"success": False, "error": str(err)}, status=500)

    async def handle_register(self, request: web.Request) -> web.Response:
        """Handle device registration."""
        try:
            data = await request.json()
            device_id = data.get("deviceid", "").strip().upper()

            if device_id in TEST_DEVICES:
                _LOGGER.info("Register: Device %s registered successfully", device_id)
                return web.json_response({"success": True, "deviceid": device_id})
            else:
                _LOGGER.warning("Register: Device %s not found", device_id)
                return web.json_response(
                    {"success": False, "error": "Device not found"}, status=404
                )

        except Exception as err:
            _LOGGER.error("Register Error: %s", err)
            return web.json_response({"success": False, "error": str(err)}, status=500)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response(
            {
                "status": "healthy",
                "devices": list(TEST_DEVICES.keys()),
                "device_count": len(TEST_DEVICES),
            }
        )

    async def start(self) -> None:
        """Start the mock API server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()

        _LOGGER.info("=" * 70)
        _LOGGER.info("Mock Mobile Alerts API Server started")
        _LOGGER.info("=" * 70)
        _LOGGER.info("Server running on: http://0.0.0.0:%d", self.port)
        _LOGGER.info("Health check: http://localhost:%d/health", self.port)
        _LOGGER.info("")
        _LOGGER.info("Available test devices:")
        for device_id, device_info in TEST_DEVICES.items():
            _LOGGER.info(
                "  - %s: %s",
                device_id,
                device_info.get("name", "Unknown"),
            )
        _LOGGER.info("")
        _LOGGER.info("Configure Home Assistant to use this mock server:")
        _LOGGER.info(
            "  export MOBILE_ALERTS_API_URL=http://localhost:%d/api/pv1/device/lastmeasurement",
            self.port,
        )
        _LOGGER.info("=" * 70)

    async def stop(self) -> None:
        """Stop the mock API server."""
        if self.runner:
            await self.runner.cleanup()
            _LOGGER.info("Mock API Server stopped")


async def run_server(port: int = 8888) -> None:
    """Run the mock API server."""
    server = MockAPIServer(port=port)
    await server.start()

    # Handle shutdown gracefully
    def signal_handler(signum: int, frame: Any) -> None:
        _LOGGER.info("Received signal %d, shutting down...", signum)
        asyncio.create_task(server.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep server running
    try:
        await asyncio.sleep(float("inf"))
    except KeyboardInterrupt:
        await server.stop()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mock Mobile Alerts API Server for testing"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MOCK_API_PORT", "8888")),
        help="Port to run the server on (default: 8888)",
    )
    args = parser.parse_args()

    asyncio.run(run_server(port=args.port))


if __name__ == "__main__":
    main()
