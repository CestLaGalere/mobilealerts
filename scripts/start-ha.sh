#!/bin/bash
# Start Mock API Server and Home Assistant for testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MOCK_SERVER_PORT=${MOCK_API_PORT:-8888}
HA_CONFIG_DIR="$PROJECT_ROOT/config"
WORKSPACE_DIR="$PROJECT_ROOT"

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

# Ask user which API to use
echo -e "${YELLOW}Which API should Home Assistant use?${NC}"
echo "  1) Mock API (for testing without real devices)"
echo "  2) Real Mobile Alerts API (requires real devices)"
echo ""
read -p "Enter choice [1-2] (default: 1): " API_CHOICE
API_CHOICE=${API_CHOICE:-1}
echo ""

USE_MOCK_API=true
if [ "$API_CHOICE" = "2" ]; then
    USE_MOCK_API=false
    echo -e "${GREEN}✓ Using real Mobile Alerts API${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Using Mock API for testing${NC}"
    echo ""
fi

# Start Mock API Server if needed
if [ "$USE_MOCK_API" = true ]; then
    # Check if mock API server is already running
    if curl -s "http://localhost:${MOCK_SERVER_PORT}/health" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Mock API server is already running on port ${MOCK_SERVER_PORT}${NC}"
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

    # Set environment variable for Mock API
    export MOBILE_ALERTS_API_URL="http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement"
    echo -e "${GREEN}✓ Environment variable set:${NC}"
    echo "  MOBILE_ALERTS_API_URL=http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement"
    echo ""
else
    # Real API - unset environment variable so integration uses default
    unset MOBILE_ALERTS_API_URL
    echo -e "${GREEN}✓ Using default Mobile Alerts API${NC}"
    echo "  (no MOBILE_ALERTS_API_URL set - using production API)"
    echo ""
fi

# Create Home Assistant config directory if it doesn't exist
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${GREEN}Creating Home Assistant config directory...${NC}"
    mkdir -p "$HA_CONFIG_DIR"
fi

# Create configuration.yaml if it doesn't exist
if [ ! -f "$HA_CONFIG_DIR/configuration.yaml" ]; then
    echo -e "${GREEN}Creating configuration.yaml...${NC}"

    # Copy appropriate default configuration based on API choice
    if [ "$USE_MOCK_API" = true ]; then
        if [ -f "$PROJECT_ROOT/tests/default_configuration mockup.yaml" ]; then
            cp "$PROJECT_ROOT/tests/default_configuration mockup.yaml" "$HA_CONFIG_DIR/configuration.yaml"
            echo -e "${GREEN}✓ Copied default mockup configuration${NC}"
        else
            echo -e "${RED}✗ Default mockup configuration not found${NC}"
            exit 1
        fi
    else
        if [ -f "$PROJECT_ROOT/tests/default_configuration live.yaml" ]; then
            cp "$PROJECT_ROOT/tests/default_configuration live.yaml" "$HA_CONFIG_DIR/configuration.yaml"
            echo -e "${GREEN}✓ Copied default live configuration${NC}"
        else
            echo -e "${RED}✗ Default live configuration not found${NC}"
            exit 1
        fi
    fi

    # Create empty automation, script, and scene files
    touch "$HA_CONFIG_DIR/automations.yaml"
    touch "$HA_CONFIG_DIR/scripts.yaml"
    touch "$HA_CONFIG_DIR/scenes.yaml"

    echo ""
fi

# Create symlink to custom_components if it doesn't exist
if [ ! -L "$HA_CONFIG_DIR/custom_components" ]; then
    echo -e "${GREEN}Creating symlink to custom_components...${NC}"
    ln -sf "$WORKSPACE_DIR/custom_components" "$HA_CONFIG_DIR/custom_components"
    echo -e "${GREEN}✓ Symlink created${NC}"
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
    # Start with env variable (if set for mock API) or without (for real API)
    if [ "$USE_MOCK_API" = true ]; then
        MOBILE_ALERTS_API_URL="http://localhost:${MOCK_SERVER_PORT}/api/pv1/device/lastmeasurement" \
        hass --config "$HA_CONFIG_DIR" --debug &
    else
        hass --config "$HA_CONFIG_DIR" --debug &
    fi
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
echo "2. Settings → Devices & Services → Add Integration"
echo "3. Search for 'Mobile Alerts' and select it"

if [ "$USE_MOCK_API" = true ]; then
    echo "4. Enter a test Device ID (see below)"
    echo ""
    echo -e "${YELLOW}Test Device IDs (Mock API):${NC}"
    echo "  090005AC99E1 - MA10100 (Thermometer)"
    echo "  090005AC99E2 - MA10200 (Thermo-Hygrometer)"
    echo "  090005AC99E3 - MA10230 (Room Climate Station)"
    echo "  107EEEB46F00 - MA10300 (Cable Sensor) ← Ambiguous with MA10350"
    echo "  107EEEB46F02 - MA10350 (Water Detector) ← Ambiguous with MA10300"
    echo "  1200099803A1 - MA10800 (Window Contact)"
    echo "  1200099803A2 - MA10880 (Wireless Switch)"
    echo ""
    echo -e "${YELLOW}Mock API Health Check:${NC}"
    echo "  curl http://localhost:${MOCK_SERVER_PORT}/health"
else
    echo "4. Enter your real Device ID from your Mobile Alerts Gateway"
    echo ""
    echo -e "${GREEN}Using real Mobile Alerts API${NC}"
    echo "  Make sure your devices are registered in the Mobile Alerts app"
fi

echo ""
echo -e "${YELLOW}To stop the servers:${NC}"
echo "  bash scripts/stop-services.sh"
echo ""
echo -e "${BLUE}========================================${NC}"
