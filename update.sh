#!/bin/bash
# =============================================================================
# Nora AI - Update Script (Linux Only)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=============================================="
echo "  Nora AI - Update"
echo -e "==============================================${NC}"
echo ""

# Linux check
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}ERROR: This script is for Linux only.${NC}"
    exit 1
fi

# Docker compose detection
COMPOSE=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo -e "${RED}ERROR: Docker Compose not found${NC}"
    exit 1
fi

# Check for native Ollama
USE_NATIVE_OLLAMA=false
if curl -s --connect-timeout 2 http://localhost:11434/api/tags &>/dev/null; then
    USE_NATIVE_OLLAMA=true
fi

# Stop services
echo -e "${BLUE}Stopping services...${NC}"
$COMPOSE down

# Pull latest code (if git repo)
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    echo -e "${BLUE}Pulling latest changes...${NC}"
    git pull
fi

# Rebuild gateway
echo -e "${BLUE}Rebuilding gateway...${NC}"
$COMPOSE build --no-cache gateway

# Start services
echo -e "${BLUE}Starting services...${NC}"
if [ "$USE_NATIVE_OLLAMA" = true ]; then
    $COMPOSE up -d gateway
else
    $COMPOSE --profile docker-ollama up -d
fi

# Wait and check
echo -e "${YELLOW}Waiting for services...${NC}"
sleep 5

if curl -s --connect-timeout 5 http://localhost:8765/health &>/dev/null; then
    echo -e "${GREEN}Update complete! Nora AI is running.${NC}"
else
    echo -e "${YELLOW}Service may still be starting. Check: docker logs nora_gateway${NC}"
fi

echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo "   View logs: docker logs -f nora_gateway"
echo "   Restart:   $COMPOSE restart"
echo ""
