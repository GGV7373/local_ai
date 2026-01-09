#!/bin/bash
# =============================================================================
# Nora AI - Advanced Setup & Deploy
# With Cloudflare Tunnel Optimization & Security
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}=============================================="
echo "  Nora AI - Advanced Setup"
echo -e "==============================================${NC}"
echo ""

# =============================================================================
# Network Information Function
# =============================================================================
get_network_info() {
    echo -e "${BLUE}📡 Detecting Network Information...${NC}"
    echo ""
    
    # Get local IP addresses
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7}' | head -1)
    
    # Get public IP (what Cloudflare will see)
    echo -e "${YELLOW}Fetching public IP (this is what Cloudflare sees)...${NC}"
    PUBLIC_IP=$(curl -s --connect-timeout 5 https://api.ipify.org 2>/dev/null || \
                curl -s --connect-timeout 5 https://ifconfig.me 2>/dev/null || \
                curl -s --connect-timeout 5 https://icanhazip.com 2>/dev/null || \
                echo "Unable to detect")
    
    # Get additional network details
    PUBLIC_IP_INFO=$(curl -s --connect-timeout 5 "https://ipinfo.io/${PUBLIC_IP}/json" 2>/dev/null || echo "{}")
    ISP=$(echo "$PUBLIC_IP_INFO" | grep -o '"org": "[^"]*"' | cut -d'"' -f4 || echo "Unknown")
    CITY=$(echo "$PUBLIC_IP_INFO" | grep -o '"city": "[^"]*"' | cut -d'"' -f4 || echo "Unknown")
    COUNTRY=$(echo "$PUBLIC_IP_INFO" | grep -o '"country": "[^"]*"' | cut -d'"' -f4 || echo "Unknown")
    
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────────┐${NC}"
    echo -e "${GREEN}│         NETWORK INFORMATION                 │${NC}"
    echo -e "${GREEN}├─────────────────────────────────────────────┤${NC}"
    echo -e "${GREEN}│${NC} Local IP:    ${CYAN}${LOCAL_IP:-Not detected}${NC}"
    echo -e "${GREEN}│${NC} Public IP:   ${CYAN}${PUBLIC_IP}${NC}"
    echo -e "${GREEN}│${NC} Location:    ${CYAN}${CITY}, ${COUNTRY}${NC}"
    echo -e "${GREEN}│${NC} ISP:         ${CYAN}${ISP}${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  This Public IP (${PUBLIC_IP}) is what Cloudflare Tunnel connects from.${NC}"
    echo -e "${YELLOW}   Make sure to whitelist it in your Cloudflare Access policies if needed.${NC}"
    echo ""
}

# =============================================================================
# System Checks
# =============================================================================
echo -e "${BLUE}🔍 Checking system requirements...${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker not installed.${NC}"
    echo "   Install: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker installed"

# Check Docker permissions
if ! docker info &> /dev/null 2>&1; then
    if sudo docker info &> /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Re-running with sudo...${NC}"
        exec sudo "$0" "$@"
    else
        echo -e "${RED}❌ ERROR: Start Docker first:${NC}"
        echo "   sudo systemctl start docker"
        exit 1
    fi
fi
echo -e "${GREEN}✓${NC} Docker running"

# Check docker compose
COMPOSE=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo -e "${RED}❌ ERROR: Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose available"

# =============================================================================
# Check for Native Ollama
# =============================================================================
USE_NATIVE_OLLAMA=false
OLLAMA_URL=""

check_native_ollama() {
    echo -e "${BLUE}🔍 Checking for Ollama...${NC}"
    
    # Check if Ollama is running on port 11434
    if curl -s --connect-timeout 2 http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${GREEN}✓${NC} Native Ollama detected on localhost:11434"
        USE_NATIVE_OLLAMA=true
        OLLAMA_URL="http://host.docker.internal:11434"
        
        # List available models
        MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | head -5)
        if [ -n "$MODELS" ]; then
            echo -e "${CYAN}   Available models:${NC}"
            echo "$MODELS" | while read model; do echo "     - $model"; done
        fi
        echo ""
        return 0
    fi
    
    # Check if Ollama command exists but not running
    if command -v ollama &>/dev/null; then
        echo -e "${YELLOW}⚠️  Ollama installed but not running.${NC}"
        echo ""
        echo "   Options:"
        echo "   1. Start native Ollama: ollama serve"
        echo "   2. Use Docker Ollama (will run in container)"
        echo ""
        read -p "Use Docker Ollama? (y/n) [y]: " USE_DOCKER_OLLAMA
        if [[ "$USE_DOCKER_OLLAMA" =~ ^[Nn]$ ]]; then
            echo -e "${YELLOW}Please start Ollama with 'ollama serve' and run setup again.${NC}"
            exit 0
        fi
        return 1
    fi
    
    # Check if port 11434 is in use by something else
    if ss -tuln 2>/dev/null | grep -q ":11434 " || netstat -tuln 2>/dev/null | grep -q ":11434 "; then
        echo -e "${RED}⚠️  Port 11434 is in use by another process.${NC}"
        echo ""
        echo "   To find what's using it:"
        echo "   sudo lsof -i :11434"
        echo "   sudo ss -tlnp | grep 11434"
        echo ""
        read -p "Try to kill the process? (y/n) [n]: " KILL_PROC
        if [[ "$KILL_PROC" =~ ^[Yy]$ ]]; then
            sudo fuser -k 11434/tcp 2>/dev/null || true
            sleep 2
        else
            echo -e "${YELLOW}Please free up port 11434 and run setup again.${NC}"
            exit 1
        fi
    fi
    
    echo -e "${CYAN}ℹ${NC}  Ollama not found - will use Docker container"
    return 1
}

check_native_ollama
echo ""

# =============================================================================
# Fix DNS Resolution (Common WSL Issue)
# =============================================================================
fix_dns() {
    echo -e "${BLUE}🌐 Checking DNS resolution...${NC}"
    
    # Test DNS
    if ! nslookup google.com &>/dev/null && ! ping -c 1 google.com &>/dev/null; then
        echo -e "${YELLOW}⚠️  DNS resolution issue detected. Attempting fix...${NC}"
        
        # Check if running in WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo -e "${CYAN}   WSL detected - applying DNS fix...${NC}"
            
            # Backup existing resolv.conf
            if [ -f /etc/resolv.conf ]; then
                sudo cp /etc/resolv.conf /etc/resolv.conf.bak 2>/dev/null || true
            fi
            
            # Create new resolv.conf with public DNS
            echo -e "# Fixed by Nora AI setup\nnameserver 8.8.8.8\nnameserver 8.8.4.4\nnameserver 1.1.1.1" | sudo tee /etc/resolv.conf > /dev/null
            
            # Prevent WSL from overwriting
            if [ -f /etc/wsl.conf ]; then
                if ! grep -q "generateResolvConf" /etc/wsl.conf; then
                    echo -e "\n[network]\ngenerateResolvConf = false" | sudo tee -a /etc/wsl.conf > /dev/null
                fi
            else
                echo -e "[network]\ngenerateResolvConf = false" | sudo tee /etc/wsl.conf > /dev/null
            fi
            
            echo -e "${GREEN}✓${NC} DNS fix applied (using Google & Cloudflare DNS)"
            echo -e "${YELLOW}   Note: Restart WSL with 'wsl --shutdown' if issues persist${NC}"
        else
            # Non-WSL Linux - suggest manual fix
            echo -e "${YELLOW}   Adding Google DNS to resolv.conf...${NC}"
            echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf > /dev/null
            echo -e "${GREEN}✓${NC} Added Google DNS"
        fi
        
        # Test again
        sleep 2
        if nslookup google.com &>/dev/null || ping -c 1 google.com &>/dev/null; then
            echo -e "${GREEN}✓${NC} DNS is now working!"
        else
            echo -e "${RED}⚠️  DNS may still have issues. Try:${NC}"
            echo "   1. Run: wsl --shutdown (from PowerShell)"
            echo "   2. Restart WSL and run setup again"
        fi
    else
        echo -e "${GREEN}✓${NC} DNS resolution working"
    fi
    echo ""
}

# Run DNS fix
fix_dns

# Create directories
mkdir -p company_info gateway/static uploads

echo ""
echo -e "${GREEN}✓ All system checks passed!${NC}"

# Show network info
get_network_info

# -----------------------------------------------------------------------------
# Quick Setup
# -----------------------------------------------------------------------------
echo -e "${BLUE}📝 Configuration${NC}"
echo ""
read -p "Company name [My Company]: " COMPANY
COMPANY=${COMPANY:-My Company}

read -p "Assistant name [Nora]: " ASSISTANT
ASSISTANT=${ASSISTANT:-Nora}

read -p "AI model (llama2/llama3/mistral) [llama2]: " MODEL
MODEL=${MODEL:-llama2}

# =============================================================================
# AI Provider Configuration
# =============================================================================
echo ""
echo -e "${BLUE}🤖 AI Provider Configuration${NC}"
echo ""
echo "Choose your AI provider:"
echo "  1. Ollama (local, free, requires GPU for best performance)"
echo "  2. Gemini (Google AI, requires API key)"
echo ""
read -p "AI Provider (1=Ollama, 2=Gemini) [1]: " AI_CHOICE
AI_CHOICE=${AI_CHOICE:-1}

GEMINI_API_KEY=""
AI_PROVIDER="ollama"

if [ "$AI_CHOICE" = "2" ]; then
    AI_PROVIDER="gemini"
    echo ""
    echo -e "${CYAN}Get your Gemini API key from:${NC}"
    echo "  https://aistudio.google.com/app/apikey"
    echo ""
    read -p "Gemini API Key: " GEMINI_API_KEY
    
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  No API key provided. Falling back to Ollama.${NC}"
        AI_PROVIDER="ollama"
    else
        echo -e "${GREEN}✓${NC} Gemini API configured"
        # Set default Gemini model
        MODEL="gemini-2.5-flash"
        read -p "Gemini model [gemini-2.5-flash]: " GEMINI_MODEL
        MODEL=${GEMINI_MODEL:-gemini-2.5-flash}
    fi
fi

# =============================================================================
# Security Configuration
# =============================================================================
echo ""
echo -e "${BLUE}🔐 Security Configuration${NC}"
echo ""

# Generate a random secret key for JWT
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 64)

read -p "Admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

echo -n "Admin password [auto-generate]: "
read -s ADMIN_PASS
echo ""
if [ -z "$ADMIN_PASS" ]; then
    ADMIN_PASS=$(openssl rand -base64 12 2>/dev/null || head -c 12 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 12)
    echo -e "${YELLOW}Generated password: ${CYAN}${ADMIN_PASS}${NC}"
    echo -e "${YELLOW}⚠️  Save this password! It won't be shown again.${NC}"
fi

echo ""
echo -e "${BLUE}☁️  Cloudflare Tunnel Configuration${NC}"
echo ""
echo "Cloudflare Tunnel provides secure public access without port forwarding."
echo -e "Get token: ${CYAN}https://one.dash.cloudflare.com${NC} → Zero Trust → Networks → Tunnels → Create"
echo ""
echo -e "${YELLOW}Note: Your tunnel will connect from IP: ${CYAN}${PUBLIC_IP}${NC}"
echo ""
read -p "Tunnel token (or press Enter to skip): " TUNNEL_TOKEN

# -----------------------------------------------------------------------------
# Create company_info files
# -----------------------------------------------------------------------------
cat > company_info/config.json << EOF
{
    "company_name": "$COMPANY",
    "assistant_name": "$ASSISTANT"
}
EOF

cat > company_info/about.txt << EOF
Company: $COMPANY
AI Assistant: $ASSISTANT

Add your company information here.
The AI will use this to answer questions about your company.
EOF

echo -e "${GREEN}✓${NC} Created company_info/"

# -----------------------------------------------------------------------------
# Create .env with enhanced security
# -----------------------------------------------------------------------------
cat > .env << EOF
# AI Configuration
AI_MODEL=$MODEL
AI_PROVIDER=$AI_PROVIDER
EOF

# Add Gemini API key if using Gemini
if [ "$AI_PROVIDER" = "gemini" ]; then
    cat >> .env << EOF
GEMINI_API_KEY=$GEMINI_API_KEY
EOF
fi

# Add Ollama URL based on native or docker (still useful as fallback)
if [ "$USE_NATIVE_OLLAMA" = true ]; then
    cat >> .env << EOF
AI_SERVER_URL=http://host.docker.internal:11434
USE_NATIVE_OLLAMA=true
EOF
else
    cat >> .env << EOF
AI_SERVER_URL=http://ollama:11434
USE_NATIVE_OLLAMA=false
EOF
fi

cat >> .env << EOF

# Security Configuration
SECRET_KEY=$SECRET_KEY
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS

# Network Info (for reference)
SERVER_PUBLIC_IP=$PUBLIC_IP
SERVER_LOCAL_IP=$LOCAL_IP
EOF

if [ -n "$TUNNEL_TOKEN" ]; then
    cat >> .env << EOF

# Cloudflare Tunnel
USE_CLOUDFLARE=true
CLOUDFLARE_TUNNEL_TOKEN=$TUNNEL_TOKEN
EOF
fi

echo -e "${GREEN}✓${NC} Created .env"

# -----------------------------------------------------------------------------
# Deploy
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"

# Build compose command with appropriate profiles
COMPOSE_PROFILES=""

# Add tunnel profile if configured
if [ -n "$TUNNEL_TOKEN" ]; then
    COMPOSE_PROFILES="$COMPOSE_PROFILES --profile tunnel"
fi

# Add docker-ollama profile if NOT using native
if [ "$USE_NATIVE_OLLAMA" != true ]; then
    COMPOSE_PROFILES="$COMPOSE_PROFILES --profile docker-ollama"
    echo -e "${CYAN}   Using Docker Ollama container${NC}"
else
    echo -e "${CYAN}   Using native Ollama on host${NC}"
fi

$COMPOSE $COMPOSE_PROFILES up -d

echo ""

# =============================================================================
# Pull AI Model with Retry
# =============================================================================
pull_model() {
    local model=$1
    local max_retries=3
    local retry=0
    
    echo -e "${BLUE}📥 Downloading AI model '$model'...${NC}"
    echo -e "${CYAN}   This may take a while depending on model size and connection speed.${NC}"
    echo ""
    
    # Use native ollama command if available, otherwise docker
    if [ "$USE_NATIVE_OLLAMA" = true ]; then
        if ollama pull $model; then
            echo -e "${GREEN}✓${NC} Model '$model' downloaded successfully!"
            return 0
        else
            echo -e "${RED}❌ Failed to download model.${NC}"
            echo "   Try manually: ollama pull $model"
            return 1
        fi
    fi
    
    # Docker-based pull with retry
    echo -e "${YELLOW}⏳ Waiting for Ollama container to start...${NC}"
    sleep 10
    
    while [ $retry -lt $max_retries ]; do
        if docker exec nora_ollama ollama pull $model; then
            echo -e "${GREEN}✓${NC} Model '$model' downloaded successfully!"
            return 0
        else
            retry=$((retry + 1))
            if [ $retry -lt $max_retries ]; then
                echo -e "${YELLOW}⚠️  Download failed. Retrying ($retry/$max_retries)...${NC}"
                echo -e "${CYAN}   Checking DNS...${NC}"
                
                # Try to fix DNS inside the container
                docker exec nora_ollama sh -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf' 2>/dev/null || true
                sleep 5
            fi
        fi
    done
    
    echo -e "${RED}❌ Failed to download model after $max_retries attempts.${NC}"
    echo -e "${YELLOW}   Common fixes:${NC}"
    echo "   1. Check internet connection"
    echo "   2. Run: wsl --shutdown (from PowerShell), then restart WSL"
    echo "   3. Try manually: docker exec -it nora_ollama ollama pull $model"
    echo ""
    return 1
}

# Only pull model if using Ollama
if [ "$AI_PROVIDER" = "ollama" ]; then
    pull_model $MODEL
else
    echo -e "${GREEN}✓${NC} Using Gemini API - no model download needed"
fi

# =============================================================================
# Cloudflare Tunnel Status
# =============================================================================
if [ -n "$TUNNEL_TOKEN" ]; then
    echo ""
    echo -e "${BLUE}☁️  Checking Cloudflare Tunnel Status...${NC}"
    sleep 5
    
    # Check if tunnel is running
    if docker ps | grep -q nora_cloudflared; then
        TUNNEL_LOGS=$(docker logs nora_cloudflared 2>&1 | tail -20)
        
        if echo "$TUNNEL_LOGS" | grep -q "Registered tunnel connection"; then
            echo -e "${GREEN}✓ Cloudflare Tunnel is connected!${NC}"
            TUNNEL_URL=$(echo "$TUNNEL_LOGS" | grep -o 'https://[^[:space:]]*\.trycloudflare\.com' | head -1 || echo "Check Cloudflare Dashboard")
            if [ -n "$TUNNEL_URL" ] && [ "$TUNNEL_URL" != "Check Cloudflare Dashboard" ]; then
                echo -e "  Public URL: ${CYAN}${TUNNEL_URL}${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Tunnel is starting... check logs: docker logs nora_cloudflared${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}┌─────────────────────────────────────────────┐${NC}"
        echo -e "${GREEN}│       CLOUDFLARE TUNNEL INFO                │${NC}"
        echo -e "${GREEN}├─────────────────────────────────────────────┤${NC}"
        echo -e "${GREEN}│${NC} Connecting From: ${CYAN}${PUBLIC_IP}${NC}"
        echo -e "${GREEN}│${NC} Local Gateway:   ${CYAN}http://gateway:8765${NC}"
        echo -e "${GREEN}│${NC} Status:          ${CYAN}docker logs nora_cloudflared${NC}"
        echo -e "${GREEN}└─────────────────────────────────────────────┘${NC}"
    else
        echo -e "${RED}❌ Tunnel container not running. Check: docker ps -a${NC}"
    fi
fi

echo ""
echo -e "${GREEN}=============================================="
echo "  ✓ Nora AI is running!"
echo -e "==============================================${NC}"
echo ""
echo -e "${GREEN}┌─────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│              ACCESS INFO                    │${NC}"
echo -e "${GREEN}├─────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│${NC} Local Web UI:  ${CYAN}http://localhost:8765${NC}"
echo -e "${GREEN}│${NC} LAN Access:    ${CYAN}http://${LOCAL_IP}:8765${NC}"
echo -e "${GREEN}├─────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│${NC} Username:      ${CYAN}${ADMIN_USER}${NC}"
echo -e "${GREEN}│${NC} Password:      ${CYAN}${ADMIN_PASS}${NC}"
echo -e "${GREEN}└─────────────────────────────────────────────┘${NC}"
if [ -n "$TUNNEL_TOKEN" ]; then
    echo ""
    echo -e "${YELLOW}☁️  Cloudflare Tunnel: Check dashboard for public URL${NC}"
    echo -e "   ${CYAN}https://one.dash.cloudflare.com${NC}"
fi
echo ""
echo -e "${BLUE}📁 Company files: ${CYAN}./company_info/${NC}"
echo "   Add your docs there - the AI will use them!"
echo ""
echo -e "${BLUE}📤 Uploaded files: ${CYAN}./uploads/${NC}"
echo "   Files uploaded via web interface are stored here."
echo ""
echo -e "${BLUE}🛠️  Commands:${NC}"
echo "    Stop:         docker compose down"
echo "    Logs:         docker compose logs -f"
echo "    Restart:      docker compose restart"
echo "    Update:       ./update.sh"
echo "    Pull model:   docker exec nora_ollama ollama pull <model>"
echo "    Tunnel logs:  docker logs nora_cloudflared -f"
echo "    Show IP:      curl -s https://api.ipify.org"
echo ""
