#!/bin/bash
# Reset Home Assistant to clean state (keeps configuration.yaml)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Reset Home Assistant${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop Home Assistant first
echo -e "${YELLOW}Stopping Home Assistant...${NC}"
bash "$SCRIPT_DIR/stop-services.sh" 2>/dev/null || true
echo ""

# Backup configuration.yaml
echo -e "${YELLOW}Backing up configuration.yaml...${NC}"
if [ -f "$CONFIG_DIR/configuration.yaml" ]; then
    cp "$CONFIG_DIR/configuration.yaml" /tmp/configuration.yaml.backup
    echo -e "${GREEN}✓ Backup created: /tmp/configuration.yaml.backup${NC}"
else
    echo -e "${RED}✗ configuration.yaml not found${NC}"
    exit 1
fi
echo ""

# Remove all Home Assistant runtime files
echo -e "${YELLOW}Removing Home Assistant runtime files...${NC}"
cd "$CONFIG_DIR"

# Remove directories
[ -d .storage ] && rm -rf .storage && echo -e "${GREEN}✓ Removed .storage${NC}"
[ -d deps ] && rm -rf deps && echo -e "${GREEN}✓ Removed deps${NC}"
[ -d blueprints ] && rm -rf blueprints && echo -e "${GREEN}✓ Removed blueprints${NC}"
[ -d custom_components ] && rm -rf custom_components && echo -e "${GREEN}✓ Removed custom_components${NC}"
[ -d tts ] && rm -rf tts && echo -e "${GREEN}✓ Removed tts${NC}"
[ -d .cloud ] && rm -rf .cloud && echo -e "${GREEN}✓ Removed .cloud${NC}"

# Remove files
[ -f home-assistant.log ] && rm -f home-assistant.log* && echo -e "${GREEN}✓ Removed log files${NC}"
[ -f home-assistant_v2.db ] && rm -f home-assistant_v2.db* && echo -e "${GREEN}✓ Removed database files${NC}"
[ -f .HA_VERSION ] && rm -f .HA_VERSION && echo -e "${GREEN}✓ Removed .HA_VERSION${NC}"
[ -f .ha_run.lock ] && rm -f .ha_run.lock && echo -e "${GREEN}✓ Removed .ha_run.lock${NC}"
[ -f .uuid ] && rm -f .uuid && echo -e "${GREEN}✓ Removed .uuid${NC}"

# Remove any YAML files except configuration.yaml
find . -maxdepth 1 -name "*.yaml" ! -name "configuration.yaml" -delete 2>/dev/null && echo -e "${GREEN}✓ Removed generated YAML files${NC}"

echo ""

# Ask user if they want to restore default configuration
echo -e "${YELLOW}Restore configuration.yaml?${NC}"
echo "  1) Keep current configuration.yaml"
echo "  2) Restore default test configuration (from tests/default_configuration.yaml)"
echo "  3) Restore from Git (git checkout)"
echo ""
read -p "Choose option [1-3] (default: 1): " RESTORE_CHOICE
RESTORE_CHOICE=${RESTORE_CHOICE:-1}
echo ""

case $RESTORE_CHOICE in
    1)
        echo -e "${GREEN}✓ Keeping current configuration.yaml${NC}"
        ;;
    2)
        if [ -f "$PROJECT_ROOT/tests/default_configuration.yaml" ]; then
            cp "$PROJECT_ROOT/tests/default_configuration.yaml" "$CONFIG_DIR/configuration.yaml"
            echo -e "${GREEN}✓ Restored default test configuration${NC}"
        else
            echo -e "${RED}✗ Default configuration not found at tests/default_configuration.yaml${NC}"
            exit 1
        fi
        ;;
    3)
        cd "$PROJECT_ROOT"
        if git checkout config/configuration.yaml 2>/dev/null; then
            echo -e "${GREEN}✓ Restored configuration.yaml from Git${NC}"
        else
            echo -e "${RED}✗ Could not restore from Git${NC}"
            echo -e "${YELLOW}Using backup instead...${NC}"
            cp /tmp/configuration.yaml.backup "$CONFIG_DIR/configuration.yaml"
        fi
        ;;
    *)
        echo -e "${RED}Invalid option, keeping current configuration${NC}"
        ;;
esac
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Home Assistant Reset Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Start Home Assistant: bash scripts/start-ha.sh"
echo "2. Open browser: http://localhost:8123"
echo "3. Create a new user account"
echo "4. Complete onboarding"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  - config/configuration.yaml (chosen option applied)"
echo ""
echo -e "${BLUE}Files removed:${NC}"
echo "  - .storage/ (user data, auth, entities)"
echo "  - home-assistant.log* (log files)"
echo "  - home-assistant_v2.db* (database)"
echo "  - .HA_VERSION, .uuid, .ha_run.lock"
echo "  - deps/, blueprints/, custom_components/"
echo ""
