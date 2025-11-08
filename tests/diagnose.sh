#!/bin/bash
# Diagnostics script for Mobile Alerts Mock API server

set -e

echo "=========================================="
echo "Mobile Alerts Mock API Diagnostics"
echo "=========================================="
echo ""

# Check if mock server is running
echo "1. Checking Mock API Server..."
if curl -s "http://localhost:8888/health" > /dev/null 2>&1; then
    echo "   ✅ Mock API Server is running on port 8888"

    # Get health status
    HEALTH=$(curl -s "http://localhost:8888/health" | python3 -m json.tool)
    echo "   Health response:"
    echo "$HEALTH" | sed 's/^/      /'
else
    echo "   ❌ Mock API Server is NOT running"
    echo "   Start it with: python3 tests/mock_api_server.py --port 8888"
fi
echo ""

# Check if Home Assistant is running
echo "2. Checking Home Assistant..."
if curl -s "http://localhost:8123" > /dev/null 2>&1; then
    echo "   ✅ Home Assistant is running on port 8123"
else
    echo "   ❌ Home Assistant is NOT running"
    echo "   Start it with: bash tests/start-test-server.sh"
fi
echo ""

# Check environment variable
echo "3. Checking environment variable..."
if [ -z "$MOBILE_ALERTS_API_URL" ]; then
    echo "   ❌ MOBILE_ALERTS_API_URL is NOT set"
    echo "   Set it with: export MOBILE_ALERTS_API_URL=\"http://localhost:8888/api/pv1/device/lastmeasurement\""
else
    echo "   ✅ MOBILE_ALERTS_API_URL is set"
    echo "   Value: $MOBILE_ALERTS_API_URL"
fi
echo ""

# Test API requests
echo "4. Testing API requests..."
echo ""

DEVICES=("090005AC99E1" "090005AC99E2" "090005AC99E3" "107EEEB46F00" "107EEEB46F02" "1200099803A1" "1200099803A2")

for device_id in "${DEVICES[@]}"; do
    echo "   Testing device: $device_id"

    RESPONSE=$(curl -s -X POST "http://localhost:8888/api/pv1/device/lastmeasurement" \
        -H "Content-Type: application/json" \
        -d "{\"deviceids\":\"$device_id\"}")

    DEVICE_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('devices', [])))" 2>/dev/null || echo "0")

    if [ "$DEVICE_COUNT" -gt 0 ]; then
        DEVICE_DATA=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); d=data.get('devices', [])[0]; print(d.get('name', 'Unknown'))" 2>/dev/null || echo "Unknown")
        echo "      ✅ OK - Got data for $DEVICE_DATA"
    else
        echo "      ❌ FAIL - No device data returned"
    fi
done
echo ""

# Summary
echo "=========================================="
echo "✅ Diagnostics complete!"
echo "=========================================="
echo ""
echo "If all checks passed:"
echo "  1. Go to http://localhost:8123"
echo "  2. Settings → Devices & Services → Create Integration"
echo "  3. Search for 'Mobile Alerts'"
echo "  4. Enter a test Device ID (e.g., 090005AC99E1)"
echo ""
echo "If checks failed:"
echo "  1. Start Mock API: python3 tests/mock_api_server.py --port 8888"
echo "  2. Start Home Assistant: bash tests/start-test-server.sh"
echo "  3. Set env variable: export MOBILE_ALERTS_API_URL=\"http://localhost:8888/api/pv1/device/lastmeasurement\""
echo ""
