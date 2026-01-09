#!/bin/bash
# =============================================================================
# Nora AI - Deployment Script for Ubuntu Server
# =============================================================================

set -e

echo "=============================================="
echo "  Nora AI - Ubuntu Server Deployment"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed. Please log out and back in, then run this script again."
    exit 0
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p gateway/static

# Copy enhanced server as main server
if [ -f "gateway/server_enhanced.py" ]; then
    cp gateway/server_enhanced.py gateway/server.py
    echo "Using enhanced server with memory support"
fi

# Start services
echo "Starting services..."
docker compose up -d

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 10

# Pull the LLM model
echo "Pulling LLM model (this may take a while)..."
docker exec nora_ollama ollama pull llama2

echo ""
echo "=============================================="
echo "  Deployment Complete!"
echo "=============================================="
echo ""
echo "Services running:"
echo "  - Gateway:   http://localhost:8765"
echo "  - Web UI:    http://localhost:8765"
echo "  - Ollama:    http://localhost:11434"
echo "  - Postgres:  localhost:5432"
echo ""
echo "To view logs:     docker compose logs -f"
echo "To stop:          docker compose down"
echo "To restart:       docker compose restart"
echo ""
