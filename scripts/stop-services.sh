#!/bin/bash
# Stop Mock API Server and Home Assistant

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping test servers...${NC}"
echo ""

# Stop Mock API Server
if [ -f /tmp/mock_api_server.pid ]; then
    PID=$(cat /tmp/mock_api_server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Mock API Server (PID: $PID)...${NC}"
        kill $PID 2>/dev/null || true
        sleep 1
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}Force killing Mock API Server...${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        rm /tmp/mock_api_server.pid
        echo -e "${GREEN}✓ Mock API Server stopped${NC}"
    else
        echo -e "${YELLOW}Mock API Server was not running${NC}"
        rm /tmp/mock_api_server.pid
    fi
else
    echo -e "${YELLOW}Mock API Server PID file not found${NC}"
fi

echo ""

# Stop Home Assistant
if [ -f /tmp/ha_server.pid ]; then
    PID=$(cat /tmp/ha_server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Home Assistant (PID: $PID)...${NC}"
        kill $PID 2>/dev/null || true
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}Force killing Home Assistant...${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        rm /tmp/ha_server.pid
        echo -e "${GREEN}✓ Home Assistant stopped${NC}"
    else
        echo -e "${YELLOW}Home Assistant was not running${NC}"
        rm /tmp/ha_server.pid
    fi
else
    echo -e "${YELLOW}Home Assistant PID file not found${NC}"
fi

echo ""

# Kill any remaining processes on the ports
echo -e "${YELLOW}Cleaning up any remaining processes...${NC}"

# Kill process on port 8123 (Home Assistant)
if command -v lsof &> /dev/null; then
    if lsof -Pi :8123 -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :8123 -sTCP:LISTEN -t)
        echo -e "${YELLOW}Found process on port 8123: $PID${NC}"
        kill $PID 2>/dev/null || true
        sleep 1
        kill -9 $PID 2>/dev/null || true
        echo -e "${GREEN}✓ Killed process on port 8123${NC}"
    fi

    # Kill process on port 8888 (Mock API Server)
    if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :8888 -sTCP:LISTEN -t)
        echo -e "${YELLOW}Found process on port 8888: $PID${NC}"
        kill $PID 2>/dev/null || true
        sleep 1
        kill -9 $PID 2>/dev/null || true
        echo -e "${GREEN}✓ Killed process on port 8888${NC}"
    fi
fi

echo ""
echo -e "${GREEN}All test servers stopped${NC}"
echo -e "${BLUE}========================================${NC}"
