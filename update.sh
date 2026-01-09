#!/bin/bash
# =============================================================================
# Nora AI - Update Script
# Pulls latest code from git and rebuilds containers
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}=============================================="
echo "  Nora AI - Update"
echo -e "==============================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed.${NC}"
    echo "   Install with: sudo apt install git"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    echo -e "${RED}❌ Not a git repository.${NC}"
    echo "   Please run this from the cloned repo directory."
    exit 1
fi

# Detect docker compose command
COMPOSE=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi

# Show current version
echo -e "${BLUE}📍 Current Status:${NC}"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "   Branch: $CURRENT_BRANCH"
echo "   Commit: $CURRENT_COMMIT"
echo ""

# Check for local changes
if ! git diff --quiet 2>/dev/null || ! git diff --staged --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  You have local changes:${NC}"
    git status --short
    echo ""
    read -p "Stash changes and continue? (y/n) [n]: " STASH_CHANGES
    if [[ "$STASH_CHANGES" =~ ^[Yy]$ ]]; then
        git stash push -m "Auto-stash before update $(date)"
        echo -e "${GREEN}✓${NC} Changes stashed"
    else
        echo -e "${YELLOW}Aborted. Commit or stash your changes first.${NC}"
        exit 0
    fi
fi

# Fetch latest
echo -e "${BLUE}🔄 Fetching latest changes...${NC}"
git fetch origin

# Check if updates available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}⚠️  No upstream branch set. Setting to origin/$CURRENT_BRANCH${NC}"
    git branch --set-upstream-to=origin/$CURRENT_BRANCH $CURRENT_BRANCH
    REMOTE=$(git rev-parse @{u})
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✓ Already up to date!${NC}"
    echo ""
    read -p "Rebuild containers anyway? (y/n) [n]: " REBUILD
    if [[ ! "$REBUILD" =~ ^[Yy]$ ]]; then
        echo "Done."
        exit 0
    fi
else
    # Show what's new
    echo ""
    echo -e "${BLUE}📋 New commits:${NC}"
    git log --oneline HEAD..@{u} | head -10
    COMMIT_COUNT=$(git rev-list --count HEAD..@{u})
    if [ "$COMMIT_COUNT" -gt 10 ]; then
        echo "   ... and $((COMMIT_COUNT - 10)) more"
    fi
    echo ""
    
    read -p "Pull updates and rebuild? (y/n) [y]: " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}📥 Pulling updates...${NC}"
        git pull --ff-only origin $CURRENT_BRANCH
        echo -e "${GREEN}✓${NC} Code updated"
    else
        echo "Aborted."
        exit 0
    fi
fi

# Rebuild and restart
echo ""
echo -e "${BLUE}🔨 Rebuilding containers...${NC}"
$COMPOSE build --no-cache gateway

echo ""
echo -e "${BLUE}🔄 Restarting services...${NC}"

# Check if using tunnel profile
if docker ps | grep -q nora_cloudflared; then
    $COMPOSE --profile tunnel up -d
else
    $COMPOSE up -d
fi

# Show new version
echo ""
NEW_COMMIT=$(git rev-parse --short HEAD)
echo -e "${GREEN}=============================================="
echo "  ✓ Update Complete!"
echo -e "==============================================${NC}"
echo ""
echo -e "   Previous: ${YELLOW}${CURRENT_COMMIT}${NC}"
echo -e "   Current:  ${GREEN}${NEW_COMMIT}${NC}"
echo ""
echo -e "${BLUE}🔍 View logs:${NC} docker compose logs -f gateway"
echo ""
