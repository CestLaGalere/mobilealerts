#!/bin/bash
# Start Home Assistant with Mobile Alerts custom component

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kill Home Assistant (port 8123) if already running
if lsof -Pi :8123 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Stopping Home Assistant (port 8123)...${NC}"
    kill $(lsof -t -i:8123) 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Home Assistant stopped${NC}"
else
    echo -e "${GREEN}Home Assistant not running${NC}"
fi

echo -e "${BLUE}Setting up Home Assistant for Mobile Alerts testing...${NC}"

# Create Home Assistant config directory
mkdir -p ~/.homeassistant

# Create symlink to custom_components
echo -e "${BLUE}Creating symlink to custom_components...${NC}"
mkdir -p ~/.homeassistant/custom_components
rm -f ~/.homeassistant/custom_components/mobile_alerts
ln -s /workspaces/mobilealerts/custom_components/mobile_alerts ~/.homeassistant/custom_components/

echo -e "${GREEN}✓ Symlink created${NC}"

# Create minimal configuration.yaml if it doesn't exist
if [ ! -f ~/.homeassistant/configuration.yaml ]; then
    echo -e "${BLUE}Creating minimal configuration.yaml...${NC}"
    cat > ~/.homeassistant/configuration.yaml << 'EOF'
# Home Assistant for Mobile Alerts Integration Testing
homeassistant:
  name: Mobile Alerts Test
  unit_system: metric
  time_zone: Europe/Zurich
  latitude: 47.0
  longitude: 8.0

# Components
frontend:
http:
logger:
  default: info
  logs:
    custom_components.mobile_alerts: debug

# Development tools
developer_tools:
EOF
    echo -e "${GREEN}✓ configuration.yaml created${NC}"
fi

# Start Home Assistant
echo -e "${BLUE}Starting Home Assistant...${NC}"
echo -e "${GREEN}Open browser: http://localhost:8123${NC}"
echo -e "${GREEN}To stop: Press Ctrl+C${NC}"

hass --config ~/.homeassistant --debug
