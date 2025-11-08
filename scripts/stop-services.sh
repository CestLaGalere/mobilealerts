#!/bin/bash
# Stop Mock Mobile Alerts API Server and Home Assistant

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Mobile Alerts Test Services...${NC}"

# Kill python mock server (port 8888)
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Stopping Mock API Server (port 8888)...${NC}"
    kill $(lsof -t -i:8888) 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Mock API Server stopped${NC}"
else
    echo -e "${GREEN}Mock API Server not running${NC}"
fi

# Kill Home Assistant (port 8123)
if lsof -Pi :8123 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Stopping Home Assistant (port 8123)...${NC}"
    kill $(lsof -t -i:8123) 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Home Assistant stopped${NC}"
else
    echo -e "${GREEN}Home Assistant not running${NC}"
fi

echo -e "${GREEN}All services stopped${NC}"
