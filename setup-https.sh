#!/bin/bash
# =============================================================================
# Nora AI - Quick HTTPS Setup for Linux
# Generates certificates and starts HTTPS server
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_DIR="$SCRIPT_DIR/nginx"
SSL_DIR="$NGINX_DIR/ssl"

echo "🚀 Nora AI - HTTPS Setup for Linux"
echo "======================================"
echo ""

# Check if running as root for some operations
if [[ $EUID -ne 0 ]]; then
   echo "⚠️  Some operations require sudo"
   echo "   You may be prompted for password"
fi

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL not found. Install with:"
    echo "   sudo apt-get install openssl"
    exit 1
fi
echo "✅ OpenSSL found"

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found"
    USE_DOCKER=true
elif command -v docker &> /dev/null; then
    echo "✅ Docker found"
    USE_DOCKER=true
else
    echo "⚠️  Docker not found (optional)"
    USE_DOCKER=false
fi

# Step 2: Create SSL directory
echo ""
echo "📁 Creating SSL directory..."
mkdir -p "$SSL_DIR"
echo "✅ SSL directory ready: $SSL_DIR"

# Step 3: Check if certificates already exist
if [ -f "$SSL_DIR/cert.pem" ] && [ -f "$SSL_DIR/key.pem" ]; then
    echo ""
    echo "⚠️  SSL certificates already exist"
    read -p "Regenerate? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates"
    else
        rm -f "$SSL_DIR"/{cert.pem,key.pem}
    fi
fi

# Step 4: Generate SSL certificates
if [ ! -f "$SSL_DIR/cert.pem" ]; then
    echo ""
    echo "🔐 Generating SSL certificates..."
    
    # Ask for server IP (optional, for certificate)
    echo ""
    read -p "Enter your server IP address (or press Enter for default): " SERVER_IP
    
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="127.0.0.1"
        echo "Using default: $SERVER_IP"
    fi
    
    # Generate certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=NO/ST=Local/L=Private/O=Nora AI/CN=nora.local" \
        -addext "subjectAltName=DNS:localhost,DNS:nora.local,IP:127.0.0.1,IP:$SERVER_IP"
    
    echo "✅ SSL certificates generated"
    echo "   Certificate: $SSL_DIR/cert.pem"
    echo "   Private key: $SSL_DIR/key.pem"
fi

# Step 5: Set proper permissions
echo ""
echo "🔒 Setting file permissions..."
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"
echo "✅ Permissions set"

# Step 6: Verify nginx config
echo ""
echo "✅ Nginx configuration is ready"
echo "   Config file: $NGINX_DIR/nginx.conf"

# Step 7: Display instructions
echo ""
echo "======================================"
echo "✅ HTTPS Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo ""

if [ "$USE_DOCKER" = true ]; then
    echo "1. Start services with Docker:"
    echo "   cd $SCRIPT_DIR"
    echo "   docker-compose up -d"
    echo ""
fi

echo "2. Access your server at:"
echo "   https://YOUR_SERVER_IP:443"
echo ""
echo "3. Accept the SSL warning (self-signed certificate)"
echo ""
echo "4. Test voice feature:"
echo "   - Click 🎤 microphone button"
echo "   - Speak something"
echo "   - Text should appear"
echo ""
echo "======================================"
echo "🎤 Voice should now work on HTTPS!"
echo "======================================"
echo ""

# Step 8: Optional - Check nginx status
if command -v systemctl &> /dev/null; then
    echo "📊 Nginx status:"
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx is running"
        echo ""
        echo "🔗 You can access it now:"
        echo "   https://localhost"
    else
        echo "⚠️  Nginx is not running"
        echo ""
        echo "To start nginx:"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
                echo "   sudo systemctl start nginx"
            elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
                echo "   sudo systemctl start nginx"
            fi
        fi
    fi
fi

echo ""
echo "For troubleshooting, see: LINUX_HTTPS_SETUP.md"
