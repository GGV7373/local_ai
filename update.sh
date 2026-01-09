#!/bin/bash
# =============================================================================
# Nora AI - Update Script (Distro-Neutral)
# Pulls latest code and rebuilds containers
# =============================================================================

set -e

echo "=============================================="
echo "  Nora AI - Update"
echo "=============================================="
echo ""

# Check for docker compose
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "ERROR: Docker Compose not found"
    exit 1
fi

# Backup user configuration
echo "Backing up your configuration..."
cp -r company_info company_info.backup 2>/dev/null || true
cp .env .env.backup 2>/dev/null || true

# Pull latest code
echo "Pulling latest code..."
git stash 2>/dev/null || true
git pull origin main

# Restore user configuration
echo "Restoring your configuration..."
cp -r company_info.backup/* company_info/ 2>/dev/null || true
cp .env.backup .env 2>/dev/null || true
rm -rf company_info.backup .env.backup 2>/dev/null || true

# Copy enhanced server
if [ -f "gateway/server_enhanced.py" ]; then
    cp gateway/server_enhanced.py gateway/server.py
fi

# Rebuild and restart containers
echo ""
echo "Rebuilding containers..."
$COMPOSE_CMD down
$COMPOSE_CMD build --no-cache gateway
$COMPOSE_CMD up -d

# Wait for Ollama and pull model if needed
echo "Waiting for Ollama..."
sleep 10

# Get model from .env or default to llama2 (POSIX-compatible)
AI_MODEL="llama2"
if [ -f ".env" ]; then
    AI_MODEL=$(grep "^AI_MODEL=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "llama2")
    AI_MODEL=${AI_MODEL:-llama2}
fi

echo "Ensuring AI model '$AI_MODEL' is available..."
docker exec nora_ollama ollama pull $AI_MODEL

echo ""
echo "=============================================="
echo "  Update Complete!"
echo "=============================================="
echo ""
echo "Your configuration (company_info/, .env) was preserved."
echo "AI Model: $AI_MODEL"
echo ""
echo "View logs: $COMPOSE_CMD logs -f"
echo ""
