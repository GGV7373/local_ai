#!/bin/bash
# =============================================================================
# Nora AI - Complete HTTPS Auto-Setup for Linux
# One script does everything - generates certs, starts services, ready to use
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_DIR="$SCRIPT_DIR/nginx"
SSL_DIR="$NGINX_DIR/ssl"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "🚀 Nora AI - Complete HTTPS Auto-Setup"
echo ""
print_info "This script will:"
echo "  1. Generate HTTPS certificates"
echo "  2. Configure nginx"
echo "  3. Start all services"
echo "  4. Test everything"
echo "  5. Show access instructions"
echo ""

# ============================================================================
# STEP 1: Check Prerequisites
# ============================================================================
print_header "STEP 1: Checking Prerequisites"

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 found"
        return 0
    else
        return 1
    fi
}

# Check OpenSSL
if ! check_command openssl; then
    print_error "OpenSSL not found!"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install openssl"
    echo "  CentOS/RHEL: sudo yum install openssl"
    exit 1
fi

# Check Docker
HAS_DOCKER=false
if check_command docker; then
    HAS_DOCKER=true
    DOCKER_COMPOSE="docker-compose"
    if ! check_command docker-compose; then
        DOCKER_COMPOSE="docker compose"  # Newer Docker versions
    fi
    print_success "Docker and Docker Compose ready"
else
    print_warning "Docker not found (will try to use system nginx)"
fi

# ============================================================================
# STEP 2: Detect Server IP
# ============================================================================
print_header "STEP 2: Detecting Server IP"

# Try to get the IP address
detect_ip() {
    # Try multiple methods to get IP
    
    # Method 1: hostname -I (works on most Linux)
    if command -v hostname &> /dev/null; then
        local ip=$(hostname -I | awk '{print $1}')
        if [ ! -z "$ip" ] && [ "$ip" != "127.0.0.1" ]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Method 2: ip command
    if command -v ip &> /dev/null; then
        local ip=$(ip route get 1 | awk '{print $7;exit}')
        if [ ! -z "$ip" ] && [ "$ip" != "127.0.0.1" ]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Method 3: ifconfig
    if command -v ifconfig &> /dev/null; then
        local ip=$(ifconfig | grep -E 'inet addr:' | grep -v '127.0.0.1' | head -1 | awk -F: '{print $2}' | awk '{print $1}')
        if [ ! -z "$ip" ]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Fallback
    echo "127.0.0.1"
}

SERVER_IP=$(detect_ip)
print_success "Detected server IP: $SERVER_IP"

# Ask if user wants to change it (with short timeout)
echo ""
read -p "Press Enter to accept IP, or type a different IP (5 second timeout): " -t 5 CUSTOM_IP || true
if [ ! -z "$CUSTOM_IP" ]; then
    SERVER_IP=$CUSTOM_IP
    print_success "Using custom IP: $SERVER_IP"
fi

# ============================================================================
# STEP 3: Generate SSL Certificates
# ============================================================================
print_header "STEP 3: Generating SSL Certificates"

mkdir -p "$SSL_DIR"

if [ -f "$SSL_DIR/cert.pem" ] && [ -f "$SSL_DIR/key.pem" ]; then
    print_warning "SSL certificates already exist"
    echo "Keeping existing certificates..."
else
    print_info "Generating new certificates for IP: $SERVER_IP"
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=NO/ST=Local/L=Private/O=Nora AI/CN=nora.local" \
        -addext "subjectAltName=DNS:localhost,DNS:nora.local,DNS:*.local,IP:127.0.0.1,IP:$SERVER_IP" \
        2>/dev/null
    
    print_success "SSL certificates generated"
fi

# Set permissions
chmod 600 "$SSL_DIR/key.pem" 2>/dev/null || sudo chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem" 2>/dev/null || sudo chmod 644 "$SSL_DIR/cert.pem"
print_success "Permissions set correctly"

# ============================================================================
# STEP 4: Start Services
# ============================================================================
print_header "STEP 4: Starting Services"

if [ "$HAS_DOCKER" = true ]; then
    print_info "Starting with Docker Compose..."
    cd "$SCRIPT_DIR"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Start services
    print_info "Starting all services (this may take a moment)..."
    $DOCKER_COMPOSE down -v 2>/dev/null || true
    $DOCKER_COMPOSE up -d 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
        sleep 3  # Give services time to start
    else
        print_error "Failed to start services"
        print_info "Trying alternative method..."
        docker compose up -d 2>/dev/null || true
    fi
    
    # Check if services are running
    if $DOCKER_COMPOSE ps 2>/dev/null | grep -q "nora_gateway"; then
        print_success "Gateway service is running"
    fi
    
    if $DOCKER_COMPOSE ps 2>/dev/null | grep -q "nora_nginx"; then
        print_success "Nginx service is running"
    fi
else
    print_warning "Docker not available, trying system nginx..."
    
    if command -v nginx &> /dev/null; then
        print_info "Starting nginx..."
        sudo nginx -c "$NGINX_DIR/nginx.conf" || sudo systemctl start nginx
        print_success "Nginx started"
    else
        print_error "Docker and nginx not found"
        echo "Please install Docker or nginx to continue"
        exit 1
    fi
fi

# ============================================================================
# STEP 5: Verify Services
# ============================================================================
print_header "STEP 5: Verifying Services"

sleep 2

# Test HTTPS connection
print_info "Testing HTTPS connection..."
if curl -s -k https://localhost:443/health &>/dev/null || curl -s -k https://localhost/health &>/dev/null; then
    print_success "HTTPS is responding"
else
    print_warning "HTTPS not responding yet (services may still be starting)"
fi

# ============================================================================
# STEP 6: Display Success and Access Info
# ============================================================================
print_header "✅ HTTPS Setup Complete!"

echo ""
echo -e "${GREEN}🎉 Everything is ready!${NC}"
echo ""
echo -e "${BLUE}📝 Access Information:${NC}"
echo ""
echo -e "  ${GREEN}URL:${NC} https://$SERVER_IP:443"
echo -e "  ${GREEN}Alt:${NC} https://localhost:443 (local)"
echo ""
echo -e "${BLUE}🔐 SSL Certificate:${NC}"
echo -e "  ${GREEN}Location:${NC} $SSL_DIR/"
echo -e "  ${GREEN}Valid for:${NC} 365 days"
echo -e "  ${GREEN}Type:${NC} Self-signed (browser warning expected)"
echo ""

# ============================================================================
# STEP 7: Test Voice Feature
# ============================================================================
print_header "STEP 7: Testing Voice Feature"

echo ""
echo -e "${BLUE}🎤 Voice Feature Status:${NC}"
echo ""
echo "  To test voice features:"
echo "    1. Open browser: ${GREEN}https://$SERVER_IP:443${NC}"
echo "    2. Login to Nora AI"
echo "    3. Click 🎤 microphone button"
echo "    4. Speak something"
echo "    5. Text should appear"
echo ""
echo "  Run diagnostic tool:"
echo "    ${GREEN}https://$SERVER_IP:443/static/voice-diagnostic.html${NC}"
echo ""

# ============================================================================
# STEP 8: Show Services Status
# ============================================================================
print_header "STEP 8: Service Status"

if [ "$HAS_DOCKER" = true ]; then
    echo ""
    print_info "Docker services status:"
    echo ""
    $DOCKER_COMPOSE ps
    echo ""
    print_info "View logs:"
    echo "  $DOCKER_COMPOSE logs -f"
    echo ""
    print_info "Stop services:"
    echo "  $DOCKER_COMPOSE down"
else
    print_info "Nginx service status:"
    sudo systemctl status nginx --no-pager | head -10
fi

# ============================================================================
# STEP 9: Final Summary
# ============================================================================
print_header "📋 Quick Reference"

echo ""
echo "Access your Nora AI:"
echo -e "  ${GREEN}https://$SERVER_IP:443${NC}"
echo ""
echo "⚠️  Browser will show SSL warning - this is normal"
echo "   Click 'Advanced' → 'Proceed' to continue"
echo ""
echo "Features now enabled:"
echo -e "  ${GREEN}✅ Voice Input${NC}     (🎤 speak to AI)"
echo -e "  ${GREEN}✅ Voice Output${NC}    (AI speaks back)"
echo -e "  ${GREEN}✅ Audio Upload${NC}    (Transcribe files)"
echo -e "  ${GREEN}✅ Chat Export${NC}     (Save conversations)"
echo -e "  ${GREEN}✅ Remote Access${NC}   (From anywhere)"
echo ""

# ============================================================================
# Additional Help
# ============================================================================
echo "Need help?"
echo ""
echo "Documentation:"
echo "  - LINUX_HTTPS_SETUP.md       (Detailed guide)"
echo "  - LINUX_DEPLOYMENT.md        (Full checklist)"
echo "  - VOICE_TROUBLESHOOTING.md   (Voice issues)"
echo ""
echo "Useful commands:"
echo "  View logs:     $DOCKER_COMPOSE logs -f"
echo "  Restart:       $DOCKER_COMPOSE restart"
echo "  Stop:          $DOCKER_COMPOSE down"
echo "  Test:          curl -k https://localhost"
echo ""

print_header "🚀 Ready to Use!"
echo ""
echo -e "Open your browser and go to:"
echo -e "  ${GREEN}https://$SERVER_IP:443${NC}"
echo ""
echo "Or use localhost (if on same machine):"
echo -e "  ${GREEN}https://localhost:443${NC}"
echo ""
print_success "Complete HTTPS setup finished!"
echo ""
