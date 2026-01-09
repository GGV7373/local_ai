#!/bin/bash
# =============================================================================
# Nora AI - SSL Setup Script (Distro-Neutral)
# Sets up Let's Encrypt SSL certificates using Docker
# =============================================================================

set -e

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

# Get domain from .env or ask
DOMAIN=""
if [ -f ".env" ]; then
    DOMAIN=$(grep "^DOMAIN=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

if [ -z "$DOMAIN" ]; then
    echo "Enter your domain name (e.g., ai.example.com):"
    read DOMAIN
fi

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Domain name required"
    exit 1
fi

# Get email
EMAIL=""
if [ -f ".env" ]; then
    EMAIL=$(grep "^SSL_EMAIL=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

if [ -z "$EMAIL" ]; then
    echo "Enter your email for Let's Encrypt notifications:"
    read EMAIL
fi

if [ -z "$EMAIL" ]; then
    echo "ERROR: Email required"
    exit 1
fi

echo ""
echo "=============================================="
echo "  SSL Setup for $DOMAIN"
echo "=============================================="
echo ""

# Create directories
mkdir -p nginx/certbot/conf
mkdir -p nginx/certbot/www

# Update nginx config with domain
if [ -f "nginx/nginx.conf.template" ]; then
    sed "s/\${DOMAIN}/$DOMAIN/g" nginx/nginx.conf.template > nginx/nginx.conf
    echo "Created nginx/nginx.conf for $DOMAIN"
fi

# Stop existing nginx if running
$COMPOSE_CMD stop nginx 2>/dev/null || true

# Get certificate using certbot docker image
echo "Requesting SSL certificate..."
docker run --rm \
    -v "$(pwd)/nginx/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/nginx/certbot/www:/var/www/certbot" \
    -p 80:80 \
    certbot/certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

# Start with SSL profile
echo ""
echo "Starting services with SSL..."
$COMPOSE_CMD --profile ssl up -d

echo ""
echo "=============================================="
echo "  SSL Setup Complete!"
echo "=============================================="
echo ""
echo "Your site is now available at:"
echo "  https://$DOMAIN"
echo ""
echo "Certificate will auto-renew."
echo ""
