#!/usr/bin/env python3
"""Test script to verify all mock API devices return proper data."""

import asyncio
import json
import sys
from tests.mock_api_server import TEST_DEVICES


async def test_devices():
    """Test all devices to ensure they have valid measurement data."""
    print("=" * 100)
    print("MOCK API SERVER - DEVICE DATA VALIDATION TEST")
    print("=" * 100)

    results = []
    all_valid = True

    for device_id, device_info in TEST_DEVICES.items():
        print(f"\n📱 Testing Device ID: {device_id}")
        print(f"   Model: {device_info['model']}")
        print(f"   Name: {device_info['name']}")

        # Check for required fields
        has_measurement = "measurement" in device_info
        print(f"   Has 'measurement' field: {has_measurement}")

        if not has_measurement:
            print("   ❌ ERROR: Missing 'measurement' field!")
            all_valid = False
            results.append(
                {
                    "device_id": device_id,
                    "model": device_info["model"],
                    "status": "❌ FAIL - Missing measurement field",
                    "keys": [],
                }
            )
        else:
            measurement = device_info["measurement"]

            # Check if measurement is not empty
            if not measurement:
                print("   ❌ ERROR: Empty measurement object!")
                all_valid = False
                results.append(
                    {
                        "device_id": device_id,
                        "model": device_info["model"],
                        "status": "❌ FAIL - Empty measurement",
                        "keys": [],
                    }
                )
            else:
                keys = list(measurement.keys())
                # Filter out metadata keys (idx, ts, c)
                data_keys = [k for k in keys if k not in ["idx", "ts", "c"]]

                print(f"   Measurement Keys: {data_keys}")
                print(f"   Data: {json.dumps(measurement, indent=15)}")

                if not data_keys:
                    print("   ⚠️ WARNING: No actual sensor data (only metadata)")
                    results.append(
                        {
                            "device_id": device_id,
                            "model": device_info["model"],
                            "status": "⚠️ WARNING - Only metadata",
                            "keys": keys,
                        }
                    )
                else:
                    print("   ✅ OK - Valid measurement data")
                    results.append(
                        {
                            "device_id": device_id,
                            "model": device_info["model"],
                            "status": "✅ OK",
                            "keys": data_keys,
                        }
                    )

    # Print summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    for result in results:
        print(
            f"{result['status']} | {result['device_id']:15} | {result['model']:10} | Keys: {result['keys']}"
        )

    print("\n" + "=" * 100)

    if all_valid:
        print("✅ All devices are valid!")
        return 0
    else:
        print("❌ Some devices have issues!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_devices()))
