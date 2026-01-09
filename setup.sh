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
AI_PROVIDER=ollama

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

if [ -n "$TUNNEL_TOKEN" ]; then
    $COMPOSE --profile tunnel up -d
else
    $COMPOSE up -d
fi

echo ""
echo -e "${YELLOW}⏳ Waiting for Ollama to start...${NC}"
sleep 10

echo -e "${BLUE}📥 Downloading AI model '$MODEL'...${NC}"
docker exec nora_ollama ollama pull $MODEL

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
echo "    Tunnel logs:  docker logs nora_cloudflared -f"
echo "    Show IP:      curl -s https://api.ipify.org"
echo ""
