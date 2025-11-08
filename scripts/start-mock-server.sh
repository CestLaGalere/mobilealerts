#!/bin/bash
# Start Mock Mobile Alerts API Server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kill python mock server (port 8888) if already running
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Stopping Mock API Server (port 8888)...${NC}"
    kill $(lsof -t -i:8888) 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Mock API Server stopped${NC}"
else
    echo -e "${GREEN}Mock API Server not running${NC}"
fi

echo -e "${BLUE}Starting Mock Mobile Alerts API Server...${NC}"
echo -e "${GREEN}API Server will run on http://localhost:8888${NC}"
echo -e "${GREEN}To stop: Press Ctrl+C${NC}"
echo ""

cd /workspaces/mobilealerts

# Set environment variable for Home Assistant to use mock server
export MOBILE_ALERTS_API_URL="http://localhost:8888/api/pv1/device/lastmeasurement"

python3 tests/mock_api_server.py
