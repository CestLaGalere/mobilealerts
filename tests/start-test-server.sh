#!/bin/bash
# Start Mock API Server and Home Assistant for testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MOCK_SERVER_PORT=${MOCK_API_PORT:-8888}
HA_CONFIG_DIR="${HOME}/.homeassistant"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Mobile Alerts Integration Test Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if mock API server is already running
if curl -s "http://localhost:${MOCK_SERVER_PORT}/health" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Mock API server is already running on port ${MOCK_SERVER_PORT}${NC}"
    echo -e "${YELLOW}Use 'stop-test-server.sh' to stop it${NC}"
    echo ""
else
    echo -e "${GREEN}Starting Mock API Server...${NC}"
    cd "$PROJECT_ROOT"
    python3 tests/mock_api_server.py --port $MOCK_SERVER_PORT &
    MOCK_PID=$!
    echo $MOCK_PID > /tmp/mock_api_server.pid

    # Wait for server to start
    echo "Waiting for Mock API Server to start..."
    sleep 2

    if curl -s "http://localhost:${MOCK_SERVER_PORT}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Mock API Server started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start Mock API Server${NC}"
        exit 1
    fi
    echo ""
fi

# Set environment variable for Home Assistant
export MOBILE_ALERTS_API_URL="http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement"
echo -e "${GREEN}✓ Environment variable set:${NC}"
echo "  MOBILE_ALERTS_API_URL=http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement"
echo ""

# Create Home Assistant config directory if it doesn't exist
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${GREEN}Creating Home Assistant config directory...${NC}"
    mkdir -p "$HA_CONFIG_DIR"

    # Create minimal configuration.yaml
    cat > "$HA_CONFIG_DIR/configuration.yaml" << 'EOF'
# Home Assistant configuration for testing Mobile Alerts Integration
homeassistant:
  name: Mobile Alerts Test
  latitude: 47.5162
  longitude: 8.7275
  elevation: 430
  unit_system: metric
  time_zone: Europe/Zurich

# Enable the web interface
http:
  server_port: 8123

# Text to speech
tts:
  - platform: google_translate

# Automation and Script
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

# Logger configuration for debugging
logger:
  default: info
  logs:
    custom_components.mobile_alerts: debug
    homeassistant.components.mobile_alerts: debug
EOF

    # Create empty automation, script, and scene files
    touch "$HA_CONFIG_DIR/automations.yaml"
    touch "$HA_CONFIG_DIR/scripts.yaml"
    touch "$HA_CONFIG_DIR/scenes.yaml"

    echo -e "${GREEN}✓ Created minimal Home Assistant configuration${NC}"
    echo ""
fi

# Check if Home Assistant is already running
if curl -s "http://localhost:8123" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Home Assistant is already running on port 8123${NC}"
    echo -e "${BLUE}Opening browser in 2 seconds...${NC}"
    sleep 2
else
    echo -e "${GREEN}Starting Home Assistant...${NC}"
    echo "Config directory: $HA_CONFIG_DIR"
    echo ""

    # Start Home Assistant with proper environment variable passing
    cd "$HA_CONFIG_DIR"
    # Start with env variable explicitly set
    MOBILE_ALERTS_API_URL="http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement" \
    hass --config "$HA_CONFIG_DIR" --debug &
    HA_PID=$!
    echo $HA_PID > /tmp/ha_server.pid

    # Wait for Home Assistant to start
    echo "Waiting for Home Assistant to start (this may take 30-60 seconds)..."
    WAIT_COUNT=0
    while ! curl -s "http://localhost:8123" > /dev/null 2>&1; do
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
        if [ $WAIT_COUNT -gt 120 ]; then
            echo -e "${RED}✗ Home Assistant failed to start${NC}"
            exit 1
        fi
        echo -ne "\rWaiting... ${WAIT_COUNT}s"
    done
    echo ""
    echo -e "${GREEN}✓ Home Assistant started successfully${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Test Environment Ready!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Home Assistant UI: http://localhost:8123"
echo "2. Settings → Devices & Services → Create Integration"
echo "3. Search for 'Mobile Alerts' and select it"
echo "4. Enter a test Device ID (e.g., 107EEEB46F02 for MA10350)"
echo ""
echo -e "${YELLOW}Test Device IDs:${NC}"
echo "  090005AC99E1 - MA10100 (Thermometer)"
echo "  090005AC99E2 - MA10200 (Thermo-Hygrometer)"
echo "  090005AC99E3 - MA10230 (Room Climate Station)"
echo "  107EEEB46F00 - MA10300 (Cable Sensor) ← Ambiguous with MA10350"
echo "  107EEEB46F02 - MA10350 (Water Detector) ← Ambiguous with MA10300"
echo "  1200099803A1 - MA10800 (Window Contact)"
echo "  1200099803A2 - MA10880 (Wireless Switch)"
echo ""
echo -e "${YELLOW}API Health Check:${NC}"
echo "  curl http://localhost:${MOCK_SERVER_PORT}/health"
echo ""
echo -e "${YELLOW}To stop the servers:${NC}"
echo "  bash tests/stop-test-server.sh"
echo ""
echo -e "${BLUE}========================================${NC}"
