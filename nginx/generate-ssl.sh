#!/bin/bash
# =============================================================================
# Generate self-signed SSL certificates for Nora AI
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/ssl"

mkdir -p "$SSL_DIR"

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/C=NO/ST=Local/L=Private/O=Nora AI/CN=nora.local" \
    -addext "subjectAltName=DNS:localhost,DNS:nora.local,IP:127.0.0.1"

echo "SSL certificates generated in: $SSL_DIR"
echo ""
echo "Files:"
echo "  - $SSL_DIR/cert.pem (certificate)"
echo "  - $SSL_DIR/key.pem (private key)"
echo ""
echo "To use HTTPS, start with:"
echo "  docker compose --profile ssl up -d"
