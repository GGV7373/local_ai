#!/bin/bash
# =============================================================================
# Nora AI - Deployment Script (Distro-Neutral)
# Works on: Debian, Ubuntu, Fedora, CentOS, Arch, Gentoo, Alpine, etc.
# =============================================================================

set -e

echo "=============================================="
echo "  Nora AI - Linux Server Deployment"
echo "=============================================="
echo ""

# Check if running as root (warn but don't fail)
if [ "$EUID" -eq 0 ]; then
    echo "Note: Running as root. Consider using a non-root user with docker group."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo ""
    echo "Please install Docker for your distribution:"
    echo ""
    echo "  Debian/Ubuntu:  curl -fsSL https://get.docker.com | sh"
    echo "  Fedora:         sudo dnf install docker docker-compose-plugin"
    echo "  Arch:           sudo pacman -S docker docker-compose"
    echo "  Gentoo:         sudo emerge app-containers/docker app-containers/docker-compose"
    echo "  Alpine:         sudo apk add docker docker-compose"
    echo ""
    echo "After installing, run: sudo systemctl enable --now docker"
    echo "Then add your user to docker group: sudo usermod -aG docker \$USER"
    echo ""
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running."
    echo ""
    echo "Start Docker with one of these commands:"
    echo "  sudo systemctl start docker    # systemd (most distros)"
    echo "  sudo rc-service docker start   # OpenRC (Gentoo, Alpine)"
    echo ""
    exit 1
fi

# Check for docker compose (v2 plugin or standalone)
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "ERROR: Docker Compose is not installed."
    echo ""
    echo "Please install Docker Compose for your distribution:"
    echo ""
    echo "  Debian/Ubuntu:  sudo apt install docker-compose-plugin"
    echo "  Fedora:         sudo dnf install docker-compose-plugin"
    echo "  Arch:           sudo pacman -S docker-compose"
    echo "  Gentoo:         sudo emerge app-containers/docker-compose"
    echo "  Alpine:         sudo apk add docker-compose"
    echo ""
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p gateway/static
mkdir -p company_info
mkdir -p nginx/certbot/conf
mkdir -p nginx/certbot/www
mkdir -p transcripts

# Create .env from example if not exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "  Edit .env to customize settings (optional)"
    echo ""
fi

# Copy enhanced server as main server
if [ -f "gateway/server_enhanced.py" ]; then
    cp gateway/server_enhanced.py gateway/server.py
    echo "Using enhanced server with memory support"
fi

# Check for Cloudflare Tunnel configuration
USE_TUNNEL="false"
TUNNEL_TOKEN=""
if [ -f ".env" ]; then
    USE_TUNNEL=$(grep "^USE_CLOUDFLARE=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "false")
    TUNNEL_TOKEN=$(grep "^CLOUDFLARE_TUNNEL_TOKEN=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

# Start services with appropriate profile
echo ""
echo "Starting services..."
if [ "$USE_TUNNEL" = "true" ] && [ -n "$TUNNEL_TOKEN" ]; then
    echo "Starting with Cloudflare Tunnel..."
    $COMPOSE_CMD --profile tunnel up -d
else
    $COMPOSE_CMD up -d
fi

# Wait for Ollama to be ready
echo ""
echo "Waiting for Ollama to start..."
sleep 10

# Get model from .env or default to llama2
AI_MODEL="llama2"
if [ -f ".env" ]; then
    # POSIX-compatible way to extract value (works on all distros)
    AI_MODEL=$(grep "^AI_MODEL=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "llama2")
    AI_MODEL=${AI_MODEL:-llama2}
fi

# Pull the LLM model
echo "Pulling LLM model '$AI_MODEL' (this may take a while)..."
docker exec nora_ollama ollama pull $AI_MODEL

echo ""
echo "=============================================="
echo "  Deployment Complete!"
echo "=============================================="
echo ""
echo "Services running:"
echo "  - Gateway:   http://localhost:8765"
echo "  - Web UI:    http://localhost:8765"
echo "  - Ollama:    http://localhost:11434"
echo "  - Postgres:  localhost:5433"

if [ "$USE_TUNNEL" = "true" ] && [ -n "$TUNNEL_TOKEN" ]; then
    DOMAIN=$(grep "^DOMAIN=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
    if [ -n "$DOMAIN" ]; then
        echo ""
        echo "Cloudflare Tunnel active!"
        echo "  - Public URL: https://$DOMAIN"
    fi
fi

echo ""
echo "AI Model: $AI_MODEL"
echo ""
echo "Commands:"
echo "  View logs:    $COMPOSE_CMD logs -f"
echo "  Stop:         $COMPOSE_CMD down"
echo "  Restart:      $COMPOSE_CMD restart"
echo ""
