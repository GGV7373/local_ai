#!/bin/bash
# =============================================================================
# Nora AI - Start/Stop Cloudflare Tunnel
# =============================================================================

# Check if Docker requires sudo
if ! docker info &> /dev/null 2>&1; then
    if sudo docker info &> /dev/null 2>&1; then
        exec sudo "$0" "$@"
    else
        echo "ERROR: Docker daemon is not running."
        exit 1
    fi
fi

# Get token from .env or command line
TOKEN=""
if [ -n "$1" ]; then
    TOKEN="$1"
elif [ -f ".env" ]; then
    TOKEN=$(grep "^CLOUDFLARE_TUNNEL_TOKEN=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

if [ -z "$TOKEN" ]; then
    echo "Usage: ./tunnel.sh [token]"
    echo ""
    echo "Or add to .env: CLOUDFLARE_TUNNEL_TOKEN=your-token"
    exit 1
fi

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

# Update .env with token if provided via command line
if [ -n "$1" ]; then
    if [ -f ".env" ]; then
        grep -v "^CLOUDFLARE_TUNNEL_TOKEN=" .env > .env.tmp && mv .env.tmp .env
        grep -v "^USE_CLOUDFLARE=" .env > .env.tmp && mv .env.tmp .env
    fi
    echo "USE_CLOUDFLARE=true" >> .env
    echo "CLOUDFLARE_TUNNEL_TOKEN=$TOKEN" >> .env
    echo "✓ Token saved to .env"
fi

echo "Starting Cloudflare Tunnel..."
$COMPOSE_CMD --profile tunnel up -d cloudflared

echo ""
echo "✓ Tunnel started!"
echo ""
echo "To view logs: docker logs -f nora_cloudflared"
echo "To stop:      docker stop nora_cloudflared"
echo ""
