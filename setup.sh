#!/bin/bash
# =============================================================================
# Nora AI - Interactive Setup Script
# Configures all settings before deployment
# =============================================================================

set -e

clear
echo "=============================================="
echo "  Nora AI - Setup Wizard"
echo "=============================================="
echo ""
echo "This script will configure your AI assistant."
echo "Press Enter to accept defaults shown in [brackets]."
echo ""

# -----------------------------------------------------------------------------
# Company Information
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  COMPANY INFORMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Company name [My Company]: " COMPANY_NAME
COMPANY_NAME=${COMPANY_NAME:-My Company}

read -p "Assistant name [Nora]: " ASSISTANT_NAME
ASSISTANT_NAME=${ASSISTANT_NAME:-Nora}

read -p "Greeting message [Hello! How can I help you today?]: " GREETING
GREETING=${GREETING:-Hello! How can I help you today?}

read -p "Primary color hex [#2563eb]: " PRIMARY_COLOR
PRIMARY_COLOR=${PRIMARY_COLOR:-#2563eb}

echo ""
echo "Enter a system prompt for the AI (what role should it play?)."
echo "Leave empty for default, or type your custom prompt:"
read -p "> " SYSTEM_PROMPT
if [ -z "$SYSTEM_PROMPT" ]; then
    SYSTEM_PROMPT="You are $ASSISTANT_NAME, a helpful AI assistant for $COMPANY_NAME. Be friendly, professional, and concise."
fi

# -----------------------------------------------------------------------------
# AI Provider
# -----------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AI PROVIDER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose your AI provider:"
echo "  1) Ollama (local, free, requires 8GB+ RAM)"
echo "  2) Google Gemini (cloud, requires API key)"
echo "  3) Both (Gemini primary, Ollama fallback)"
echo ""
read -p "Selection [1]: " AI_CHOICE
AI_CHOICE=${AI_CHOICE:-1}

GEMINI_API_KEY=""
AI_MODEL="llama2"

case $AI_CHOICE in
    2)
        AI_PROVIDER="gemini"
        echo ""
        echo "Get your Gemini API key from: https://makersuite.google.com/app/apikey"
        read -p "Gemini API Key: " GEMINI_API_KEY
        if [ -z "$GEMINI_API_KEY" ]; then
            echo "Warning: No API key provided, falling back to Ollama"
            AI_PROVIDER="ollama"
        fi
        ;;
    3)
        AI_PROVIDER="auto"
        echo ""
        echo "Get your Gemini API key from: https://makersuite.google.com/app/apikey"
        read -p "Gemini API Key: " GEMINI_API_KEY
        ;;
    *)
        AI_PROVIDER="ollama"
        echo ""
        echo "Available Ollama models:"
        echo "  - llama2 (default, 4GB)"
        echo "  - llama3 (newest, 4GB)"
        echo "  - mistral (fast, 4GB)"
        echo "  - codellama (coding, 4GB)"
        read -p "Model [llama2]: " AI_MODEL
        AI_MODEL=${AI_MODEL:-llama2}
        ;;
esac

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DATABASE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PostgreSQL stores conversation history."
echo ""

read -p "Database name [nora_db]: " DB_NAME
DB_NAME=${DB_NAME:-nora_db}

read -p "Database user [nora]: " DB_USER
DB_USER=${DB_USER:-nora}

# Generate random password if not provided
DEFAULT_DB_PASS=$(head -c 32 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 16)
read -p "Database password [$DEFAULT_DB_PASS]: " DB_PASS
DB_PASS=${DB_PASS:-$DEFAULT_DB_PASS}

# -----------------------------------------------------------------------------
# Domain & Access
# -----------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DOMAIN & SECURE ACCESS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose how to access your AI:"
echo "  1) Local only (http://localhost:8765)"
echo "  2) Cloudflare Tunnel (secure, no open ports, free SSL)"
echo "  3) Custom domain with Let's Encrypt SSL"
echo ""
read -p "Selection [1]: " ACCESS_CHOICE
ACCESS_CHOICE=${ACCESS_CHOICE:-1}

DOMAIN=""
USE_CLOUDFLARE="false"
SSL_EMAIL=""
CLOUDFLARE_TOKEN=""

case $ACCESS_CHOICE in
    2)
        USE_CLOUDFLARE="true"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  CLOUDFLARE TUNNEL SETUP"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. Go to: https://one.dash.cloudflare.com/"
        echo "2. Zero Trust → Networks → Tunnels → Create"
        echo "3. Name it (e.g., nora-ai)"
        echo "4. Copy the token (the long string)"
        echo ""
        echo "Paste your tunnel token:"
        read -p "> " CLOUDFLARE_TOKEN
        if [ -z "$CLOUDFLARE_TOKEN" ]; then
            echo "Warning: No token provided, using local access only"
            USE_CLOUDFLARE="false"
        else
            echo ""
            echo "What domain did you configure in Cloudflare?"
            read -p "Domain (e.g., ai.example.com): " DOMAIN
            echo ""
            echo "In Cloudflare tunnel config, set Service to: http://gateway:8765"
        fi
        ;;
    3)
        echo ""
        read -p "Your domain (e.g., ai.example.com): " DOMAIN
        read -p "Email for SSL certificate: " SSL_EMAIL
        ;;
esac

# -----------------------------------------------------------------------------
# Create Configuration Files
# -----------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SAVING CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create directories
mkdir -p company_info
mkdir -p gateway/static
mkdir -p nginx/certbot/conf
mkdir -p nginx/certbot/www
mkdir -p transcripts

# Create company_info/config.json
cat > company_info/config.json << EOF
{
    "company_name": "$COMPANY_NAME",
    "assistant_name": "$ASSISTANT_NAME",
    "greeting": "$GREETING",
    "primary_color": "$PRIMARY_COLOR",
    "domain": "$DOMAIN"
}
EOF
echo "✓ Created company_info/config.json"

# Create company_info/system_prompt.txt
echo "$SYSTEM_PROMPT" > company_info/system_prompt.txt
echo "✓ Created company_info/system_prompt.txt"

# Create .env file
cat > .env << EOF
# Nora AI Configuration
# Generated by setup.sh on $(date)

# =============================================================================
# Gateway Settings
# =============================================================================
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8765

# =============================================================================
# AI Provider
# =============================================================================
# Options: auto, ollama, gemini
AI_PROVIDER=$AI_PROVIDER

# Ollama (local)
AI_SERVER_URL=http://ollama:11434
AI_MODEL=$AI_MODEL

# Google Gemini (cloud)
GEMINI_API_KEY=$GEMINI_API_KEY
GEMINI_MODEL=gemini-pro

# =============================================================================
# Database
# =============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASS
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@postgres:5432/$DB_NAME

# Redis
REDIS_URL=redis://redis:6379/0

# =============================================================================
# Domain & SSL
# =============================================================================
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL

# =============================================================================
# Cloudflare Tunnel
# =============================================================================
USE_CLOUDFLARE=$USE_CLOUDFLARE
CLOUDFLARE_TUNNEL_TOKEN=$CLOUDFLARE_TOKEN
EOF
echo "✓ Created .env"

# Update docker-compose.yml for Cloudflare if selected
if [ "$USE_CLOUDFLARE" = "true" ]; then
    # Check if cloudflared service already exists
    if ! grep -q "cloudflared:" docker-compose.yml 2>/dev/null; then
        cat >> docker-compose.yml << 'EOF'

  # Cloudflare Tunnel - Secure access without opening ports
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: nora_cloudflared
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - gateway
    networks:
      - nora_network
EOF
        echo "✓ Added Cloudflare Tunnel to docker-compose.yml"
    fi
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Configuration Summary:"
echo "  Company:     $COMPANY_NAME"
echo "  Assistant:   $ASSISTANT_NAME"
echo "  AI Provider: $AI_PROVIDER"
if [ "$AI_PROVIDER" = "ollama" ] || [ "$AI_PROVIDER" = "auto" ]; then
    echo "  AI Model:    $AI_MODEL"
fi
echo "  Database:    $DB_NAME"

if [ "$USE_CLOUDFLARE" = "true" ]; then
    echo "  Access:      Cloudflare Tunnel"
    echo "  URL:         https://$DOMAIN"
elif [ -n "$DOMAIN" ]; then
    echo "  Access:      Custom domain with SSL"
    echo "  URL:         https://$DOMAIN"
else
    echo "  Access:      Local only"
    echo "  URL:         http://localhost:8765"
fi

# -----------------------------------------------------------------------------
# Deploy Now?
# -----------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Start the AI now? [Y/n]: " DEPLOY_NOW
DEPLOY_NOW=${DEPLOY_NOW:-Y}

if [[ "$DEPLOY_NOW" =~ ^[Yy]$ ]] || [ -z "$DEPLOY_NOW" ]; then
    echo ""
    echo "Starting deployment..."
    echo ""
    ./deploy.sh
else
    echo ""
    echo "To deploy later, run: ./deploy.sh"
    echo ""
    if [ "$USE_CLOUDFLARE" = "true" ]; then
        echo "Remember to configure your Cloudflare Tunnel to point to:"
        echo "  http://gateway:8765"
    elif [ -n "$DOMAIN" ] && [ -n "$SSL_EMAIL" ]; then
        echo "After deploying, run: ./setup_ssl.sh"
    fi
    echo ""
fi
