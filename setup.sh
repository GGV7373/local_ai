#!/bin/bash
# =============================================================================
# Nora AI - Linux Private Server Setup
# No cloud dependencies - Direct IP access only
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
echo "  Nora AI - Linux Private Server Setup"
echo -e "==============================================${NC}"
echo ""

# =============================================================================
# Linux Check
# =============================================================================
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}ERROR: This setup script is for Linux only.${NC}"
    echo "   Detected OS: $OSTYPE"
    exit 1
fi

# =============================================================================
# Get Local Network Info (No external API calls)
# =============================================================================
get_local_network_info() {
    echo -e "${BLUE}Detecting Local Network...${NC}"
    echo ""
    
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7}' | head -1)
    
    echo -e "${GREEN}LOCAL NETWORK INFORMATION${NC}"
    echo -e "  Local IP:    ${CYAN}${LOCAL_IP:-Not detected}${NC}"
    echo -e "  Hostname:    ${CYAN}$(hostname)${NC}"
    echo ""
    echo -e "${YELLOW}Access Nora AI at: http://${LOCAL_IP}:8765${NC}"
    echo ""
}

# =============================================================================
# Check GPU
# =============================================================================
check_gpu() {
    echo -e "${BLUE}Checking GPU Support...${NC}"
    
    if command -v nvidia-smi &>/dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            echo -e "${GREEN}NVIDIA GPU detected: ${CYAN}$GPU_INFO${NC}"
            GPU_TYPE="nvidia"
            return 0
        fi
    fi
    
    if command -v rocm-smi &>/dev/null; then
        if rocm-smi --showproductname &>/dev/null; then
            echo -e "${GREEN}AMD GPU detected (ROCm)${NC}"
            GPU_TYPE="amd"
            return 0
        fi
    fi
    
    echo -e "${YELLOW}No GPU detected - Ollama will use CPU${NC}"
    GPU_TYPE="none"
}

# =============================================================================
# System Checks
# =============================================================================
echo -e "${BLUE}Checking system requirements...${NC}"
echo ""

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not installed.${NC}"
    echo "   Install: curl -fsSL https://get.docker.com | sh"
    echo "   Then: sudo usermod -aG docker \$USER"
    exit 1
fi
echo -e "${GREEN}Docker installed${NC}"

if ! docker info &> /dev/null 2>&1; then
    if sudo docker info &> /dev/null 2>&1; then
        echo -e "${YELLOW}Re-running with sudo...${NC}"
        exec sudo "$0" "$@"
    else
        echo -e "${RED}ERROR: Start Docker first: sudo systemctl start docker${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Docker running${NC}"

COMPOSE=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo -e "${RED}ERROR: Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}Docker Compose available${NC}"

check_gpu
echo ""

# =============================================================================
# Ollama Setup
# =============================================================================
USE_NATIVE_OLLAMA=false
OLLAMA_URL=""

install_ollama() {
    echo -e "${BLUE}Installing Ollama...${NC}"
    
    if curl -fsSL https://ollama.com/install.sh | sh; then
        echo -e "${GREEN}Ollama installed successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to install Ollama${NC}"
        return 1
    fi
}

configure_ollama_systemd() {
    echo -e "${BLUE}Configuring Ollama for network access...${NC}"
    
    sudo mkdir -p /etc/systemd/system/ollama.service.d/
    cat << EOF | sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_ORIGINS=*"
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    sleep 2
    
    if systemctl is-active --quiet ollama 2>/dev/null; then
        echo -e "${GREEN}Ollama configured and restarted${NC}"
        return 0
    else
        echo -e "${YELLOW}Could not restart Ollama via systemd${NC}"
        return 1
    fi
}

start_ollama() {
    echo -e "${BLUE}Starting Ollama service...${NC}"
    
    if command -v systemctl &>/dev/null; then
        sudo systemctl start ollama 2>/dev/null || true
        sudo systemctl enable ollama 2>/dev/null || true
        sleep 3
        
        if systemctl is-active --quiet ollama 2>/dev/null; then
            echo -e "${GREEN}Ollama service started${NC}"
            return 0
        fi
    fi
    
    echo -e "${YELLOW}Starting Ollama in background...${NC}"
    OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    
    if curl -s --connect-timeout 2 http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${GREEN}Ollama is now running${NC}"
        return 0
    else
        echo -e "${RED}Failed to start Ollama${NC}"
        return 1
    fi
}

pull_model() {
    local model=$1
    echo -e "${BLUE}Downloading model: ${CYAN}$model${NC}..."
    
    if ollama list 2>/dev/null | grep -q "$model"; then
        echo -e "${GREEN}Model $model is already installed!${NC}"
        return 0
    fi
    
    if ollama pull "$model"; then
        echo -e "${GREEN}Model $model downloaded successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to download model $model${NC}"
        return 1
    fi
}

check_native_ollama() {
    echo -e "${BLUE}Checking for Ollama...${NC}"
    
    if curl -s --connect-timeout 2 http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${GREEN}Ollama is running on localhost:11434${NC}"
        USE_NATIVE_OLLAMA=true
        OLLAMA_URL="http://host.docker.internal:11434"
        
        OLLAMA_BIND=$(ss -tlnp 2>/dev/null | grep ":11434" | head -1)
        if echo "$OLLAMA_BIND" | grep -q "127.0.0.1:11434"; then
            echo -e "${YELLOW}Ollama is only listening on localhost${NC}"
            read -p "Configure Ollama for network access? (y/n) [y]: " FIX_BINDING
            FIX_BINDING=${FIX_BINDING:-y}
            
            if [[ "$FIX_BINDING" =~ ^[Yy]$ ]]; then
                configure_ollama_systemd
            fi
        fi
        
        MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | head -5)
        if [ -n "$MODELS" ]; then
            echo -e "${CYAN}Available models:${NC}"
            echo "$MODELS" | while read model; do echo "  - $model"; done
        fi
        return 0
    fi
    
    if command -v ollama &>/dev/null; then
        echo -e "${YELLOW}Ollama installed but not running.${NC}"
        read -p "Start Ollama now? (y/n) [y]: " START_OLLAMA
        START_OLLAMA=${START_OLLAMA:-y}
        
        if [[ "$START_OLLAMA" =~ ^[Yy]$ ]]; then
            if start_ollama; then
                USE_NATIVE_OLLAMA=true
                OLLAMA_URL="http://host.docker.internal:11434"
                return 0
            fi
        fi
        return 1
    fi
    
    echo -e "${CYAN}Ollama not found on your system.${NC}"
    read -p "Install Ollama now? (y/n) [y]: " INSTALL_OLLAMA
    INSTALL_OLLAMA=${INSTALL_OLLAMA:-y}
    
    if [[ "$INSTALL_OLLAMA" =~ ^[Yy]$ ]]; then
        if install_ollama; then
            configure_ollama_systemd
            if start_ollama; then
                USE_NATIVE_OLLAMA=true
                OLLAMA_URL="http://host.docker.internal:11434"
                return 0
            fi
        fi
    fi
    
    echo -e "${CYAN}Will use Docker Ollama container instead${NC}"
    return 1
}

check_native_ollama
echo ""

mkdir -p company_info gateway/static uploads nginx/ssl

echo -e "${GREEN}System checks passed!${NC}"
echo ""

get_local_network_info

# =============================================================================
# Configuration
# =============================================================================
echo -e "${BLUE}Configuration${NC}"
echo ""

DEFAULT_SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p | tr -d '\n' | head -c 64)
DEFAULT_PASSWORD=$(openssl rand -base64 12 2>/dev/null || head -c 16 /dev/urandom | base64 | head -c 12)

read -p "Admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

read -p "Admin password [auto-generated]: " ADMIN_PASS
ADMIN_PASS=${ADMIN_PASS:-$DEFAULT_PASSWORD}

echo ""
echo -e "${CYAN}Select AI Provider:${NC}"
echo "  1) Ollama (Local - Recommended)"
echo "  2) Google Gemini (Cloud API)"
echo "  3) Both (Ollama primary, Gemini fallback)"
read -p "Choice [1]: " AI_CHOICE
AI_CHOICE=${AI_CHOICE:-1}

AI_PROVIDER="ollama"
GEMINI_KEY=""
GEMINI_MODEL="gemini-2.0-flash"

case $AI_CHOICE in
    2)
        AI_PROVIDER="gemini"
        read -p "Gemini API Key: " GEMINI_KEY
        echo ""
        echo -e "${CYAN}Select Gemini Model:${NC}"
        echo "  1) gemini-2.0-flash (Fast, recommended)"
        echo "  2) gemini-2.5-flash-preview-05-20 (Latest)"
        echo "  3) gemini-1.5-pro (Larger context)"
        read -p "Choice [1]: " GEMINI_CHOICE
        case $GEMINI_CHOICE in
            2) GEMINI_MODEL="gemini-2.5-flash-preview-05-20" ;;
            3) GEMINI_MODEL="gemini-1.5-pro" ;;
            *) GEMINI_MODEL="gemini-2.0-flash" ;;
        esac
        ;;
    3)
        AI_PROVIDER="ollama"
        read -p "Gemini API Key (for fallback): " GEMINI_KEY
        ;;
esac

OLLAMA_MODEL="llama3.2"
if [ "$AI_PROVIDER" == "ollama" ] || [ "$AI_CHOICE" == "3" ]; then
    echo ""
    echo -e "${CYAN}Select Ollama Model:${NC}"
    echo "  1) llama3.2 (Recommended, 3B)"
    echo "  2) llama3.2:1b (Smaller, faster)"
    echo "  3) mistral (7B)"
    echo "  4) gemma2 (9B)"
    echo "  5) codellama (For coding)"
    echo "  6) Custom"
    read -p "Choice [1]: " MODEL_CHOICE
    
    case $MODEL_CHOICE in
        2) OLLAMA_MODEL="llama3.2:1b" ;;
        3) OLLAMA_MODEL="mistral" ;;
        4) OLLAMA_MODEL="gemma2" ;;
        5) OLLAMA_MODEL="codellama" ;;
        6) read -p "Model name: " OLLAMA_MODEL ;;
        *) OLLAMA_MODEL="llama3.2" ;;
    esac
    
    if [ "$USE_NATIVE_OLLAMA" = true ]; then
        pull_model "$OLLAMA_MODEL"
    fi
fi

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo -e "${BLUE}Creating configuration files...${NC}"

cat > .env << EOF
# Nora AI - Configuration
# Generated: $(date)

# AI Configuration
AI_PROVIDER=${AI_PROVIDER}
AI_MODEL=${OLLAMA_MODEL}
AI_SERVER_URL=${OLLAMA_URL:-http://host.docker.internal:11434}

# Gemini Configuration
GEMINI_API_KEY=${GEMINI_KEY}
GEMINI_MODEL=${GEMINI_MODEL}

# Security
SECRET_KEY=${DEFAULT_SECRET}
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}

# Server
GATEWAY_PORT=8765
SERVER_IP=${LOCAL_IP}
EOF

echo -e "${GREEN}Created .env file${NC}"

echo ""
echo -e "${BLUE}Firewall Configuration${NC}"

if command -v ufw &>/dev/null; then
    read -p "Configure UFW firewall? (y/n) [n]: " SETUP_UFW
    if [[ "$SETUP_UFW" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Allowing port 8765 (Nora AI)...${NC}"
        sudo ufw allow 8765/tcp comment "Nora AI"
        echo -e "${GREEN}Firewall configured${NC}"
    fi
elif command -v firewall-cmd &>/dev/null; then
    read -p "Configure firewalld? (y/n) [n]: " SETUP_FIREWALLD
    if [[ "$SETUP_FIREWALLD" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Allowing port 8765 (Nora AI)...${NC}"
        sudo firewall-cmd --permanent --add-port=8765/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}Firewall configured${NC}"
    fi
else
    echo -e "${YELLOW}No firewall manager detected (ufw/firewalld)${NC}"
fi

echo ""
echo -e "${BLUE}Starting Nora AI...${NC}"
echo ""

if [ "$USE_NATIVE_OLLAMA" = true ]; then
    echo -e "${CYAN}Using native Ollama installation${NC}"
    $COMPOSE up -d gateway
else
    echo -e "${CYAN}Using Docker Ollama container${NC}"
    $COMPOSE --profile docker-ollama up -d
fi

echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

if curl -s --connect-timeout 5 http://localhost:8765/health &>/dev/null; then
    echo -e "${GREEN}Nora AI is running!${NC}"
else
    echo -e "${YELLOW}Service may still be starting. Check: docker logs nora_gateway${NC}"
fi

echo ""
echo -e "${GREEN}=============================================="
echo "  Nora AI Setup Complete!"
echo -e "==============================================${NC}"
echo ""
echo -e "${CYAN}Access your AI assistant:${NC}"
echo -e "   URL:       ${GREEN}http://${LOCAL_IP}:8765${NC}"
echo -e "   Username:  ${GREEN}${ADMIN_USER}${NC}"
echo -e "   Password:  ${GREEN}${ADMIN_PASS}${NC}"
echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo "   View logs:     docker logs -f nora_gateway"
echo "   Stop:          $COMPOSE down"
echo "   Restart:       $COMPOSE restart"
echo "   Update:        git pull && $COMPOSE up -d --build"
echo ""
if [ "$USE_NATIVE_OLLAMA" = true ]; then
    echo -e "${CYAN}Ollama commands:${NC}"
    echo "   List models:   ollama list"
    echo "   Pull model:    ollama pull <model>"
    echo "   Service:       sudo systemctl status ollama"
fi
echo ""
