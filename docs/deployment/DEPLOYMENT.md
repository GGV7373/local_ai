# Deployment Guide - Nora AI

Complete guide for deploying Nora AI on Linux servers with HTTPS support.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Generate HTTPS Certificates
```bash
cd /path/to/local_ai
bash setup-https.sh
```

This will:
- ✅ Check prerequisites (openssl)
- ✅ Create SSL directory
- ✅ Generate self-signed certificates
- ✅ Ask for your server IP (optional)
- ✅ Set proper permissions
- ✅ Show next steps

### Step 2: Start Your Services
```bash
# Using Docker Compose
docker-compose up -d

# Or if using Docker directly
docker-compose --profile ssl up -d
```

### Step 3: Access & Test
```
Open browser: https://YOUR_SERVER_IP:443
```

---

## 📋 Prerequisites

Make sure you have:
```bash
openssl          # For certificate generation
docker           # For running containers
docker-compose   # For orchestration
```

Check if installed:
```bash
openssl version
docker --version
docker-compose --version
```

---

## 📦 Basic Deployment

### File Structure
Your project should have:
```
local_ai/
├── nginx/
│   ├── nginx.conf          # Proxy config
│   ├── generate-ssl.sh     # Certificate generator
│   └── ssl/                # SSL directory (created by script)
│       ├── cert.pem        # Certificate
│       └── key.pem         # Private key
├── gateway/
│   ├── server.py
│   ├── Dockerfile
│   └── ...
├── docker-compose.yml      # Orchestration config
├── setup-https.sh          # Quick setup script
└── docs/                   # Documentation
```

### Docker Compose Setup

Your `docker-compose.yml` should include an nginx service:

```yaml
version: '3.8'

services:
  gateway:
    # ... your existing gateway config ...
    ports:
      - "8765:8765"
    networks:
      - nora_network

  nginx:
    image: nginx:latest
    container_name: nora_nginx
    restart: unless-stopped
    ports:
      - "80:80"      # HTTP (redirects to HTTPS)
      - "443:443"    # HTTPS
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - nora_network
    depends_on:
      - gateway

networks:
  nora_network:
    driver: bridge

volumes:
  ollama_data:
```

---

## 🔐 HTTPS Setup

### Why HTTPS is Required

With HTTPS enabled on Linux:

| Feature | HTTP | HTTPS |
|---------|------|-------|
| 🎤 Voice Input | ❌ Blocked | ✅ Works |
| 🔊 Voice Output | ❌ Blocked | ✅ Works |
| 🎵 Audio Upload | ✅ Works | ✅ Works |
| 💾 Chat Export | ✅ Works | ✅ Works |
| 📁 File Upload | ✅ Works | ✅ Works |
| 🌐 Remote Access | ✅ Works | ✅ Works |

**TL;DR:** Voice features require HTTPS for security. Browsers block microphone access over HTTP.

### Step 1: Generate SSL Certificates

Run the provided script to generate self-signed certificates:

```bash
cd /path/to/local_ai
bash setup-https.sh
```

Or manually:
```bash
cd nginx
bash generate-ssl.sh
cd ..
```

This creates:
- `nginx/ssl/cert.pem` - Certificate
- `nginx/ssl/key.pem` - Private key

The certificates are valid for 365 days and work with:
- localhost
- nora.local
- 127.0.0.1
- Any IP address (added to certificate)

### Step 2: Configure Server IP (Optional)

The default certificate works for any IP. For best results with your specific IP:

Edit `nginx/generate-ssl.sh` and update this line:

```bash
# Change this line:
-addext "subjectAltName=DNS:localhost,DNS:nora.local,IP:127.0.0.1"

# To include your server IP:
-addext "subjectAltName=DNS:localhost,DNS:nora.local,IP:127.0.0.1,IP:YOUR.SERVER.IP.HERE"
```

Then regenerate:
```bash
bash generate-ssl.sh
```

### Step 3: Update Nginx Configuration

Ensure `nginx/nginx.conf` has correct paths:
- SSL certificates path: `/etc/nginx/ssl/`
- Upstream gateway correct: `gateway:8765`
- Server name allows all: `server_name _;`

### Step 4: Start Services

```bash
# If using Docker Compose
docker-compose up -d

# If running natively (on Ubuntu/Debian)
sudo nginx -c /path/to/local_ai/nginx/nginx.conf

# Verify nginx is running
sudo systemctl status nginx
```

### Step 5: Access Your Server

After setup, access via:

```
https://YOUR_SERVER_IP:443
```

Examples:
- `https://192.168.1.100:443`
- `https://10.0.0.50:443`
- `https://your-domain.com:443` (if using domain)

---

## 📋 Full Deployment Checklist

### Pre-Deployment
- [ ] Linux server ready (Ubuntu/Debian/CentOS)
- [ ] SSH access to server
- [ ] Know your server's IP address
- [ ] OpenSSL installed: `openssl version`
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`

### Certificate Generation
- [ ] Navigate to project directory: `cd /path/to/local_ai`
- [ ] Run setup script: `bash setup-https.sh`
- [ ] Verify certificates: `ls -la nginx/ssl/`
  - Should show: `cert.pem` and `key.pem`

### Docker Setup
- [ ] Review `docker-compose.yml`
- [ ] Nginx service configured
- [ ] Ports open: 80 (HTTP) and 443 (HTTPS)
- [ ] Volumes mounted correctly
- [ ] Networks configured

### Firewall/Network
- [ ] Port 80 open (HTTP → HTTPS redirect)
- [ ] Port 443 open (HTTPS)
- [ ] Server IP is accessible from client
- [ ] No firewall blocking ports

### Starting Services
- [ ] Run: `docker-compose up -d`
- [ ] Check status: `docker-compose ps`
- [ ] All containers running (gateway, nginx, etc.)

### Testing
- [ ] HTTPS accessible: `https://SERVER_IP`
- [ ] HTTP redirects to HTTPS: `http://SERVER_IP`
- [ ] Login page loads
- [ ] Run diagnostic: `https://SERVER_IP/static/voice-diagnostic.html`
- [ ] Voice input works (🎤 button)
- [ ] Voice output works (AI speaks)

### Post-Deployment
- [ ] Set up monitoring/logs
- [ ] Configure backups
- [ ] Document IP and access info
- [ ] Test all features
- [ ] Create user accounts

---

## 🚀 Command Reference

### Setup Commands
```bash
# Run setup script
bash setup-https.sh

# Or manually generate certificates
cd nginx
bash generate-ssl.sh
cd ..
```

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v

# Restart a specific service
docker-compose restart nginx
```

### Monitoring
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f nginx
docker-compose logs -f gateway

# Check container status
docker-compose ps

# Check nginx configuration
docker exec nora_nginx nginx -T

# Test nginx config
docker exec nora_nginx nginx -t
```

### Troubleshooting
```bash
# View nginx error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log

# Test HTTPS connection
curl -k https://localhost:443

# Check open ports
sudo netstat -tlnp | grep -E ':(80|443)'

# Check if gateway is responding
curl http://localhost:8765/health

# Find what's using port 443
sudo lsof -i :443
```

---

## 🔐 SSL Certificate Management

### Self-Signed Certificates
- **Generated by:** OpenSSL
- **Valid for:** 365 days
- **Type:** RSA 2048-bit
- **Subject:** Nora AI
- **Locations:** `nginx/ssl/`

### Browser Security Warnings
- Browsers will show ⚠️ warning for self-signed certificates
- This is normal and expected
- Click "Advanced" → "Proceed" to continue
- Voice features work despite the warning

### Renewing Certificates

Certificates expire after 365 days. Regenerate them:

```bash
# Remove old certificates
rm -rf nginx/ssl/*

# Regenerate
bash setup-https.sh

# Restart nginx
docker-compose restart nginx
```

---

## 🏭 Production Deployment

### Upgrade to Let's Encrypt Certificates

For production use, upgrade to trusted certificates:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate free certificate (requires domain name)
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx.conf to use these certificates:
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Restart nginx
docker-compose restart nginx
```

### Auto-Renewal Setup

Let's Encrypt certificates expire every 90 days:

```bash
# Test renewal
sudo certbot renew --dry-run

# Set up auto-renewal (cron job)
sudo crontab -e

# Add this line (runs daily at 2am)
0 2 * * * certbot renew --quiet && docker-compose restart nginx
```

### Security Best Practices

1. **Use strong SSL configuration**
   - TLS 1.2 and 1.3 only
   - Strong cipher suites
   - HSTS headers

2. **Keep software updated**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. **Configure firewall**
   ```bash
   # UFW (Ubuntu)
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

4. **Regular backups**
   - Backup `company_info/` directory
   - Backup `uploads/` directory
   - Export conversations regularly

5. **Monitor logs**
   ```bash
   # Set up log rotation
   sudo nano /etc/logrotate.d/nora-ai
   ```

---

## 🛠️ Troubleshooting

### "Connection refused"
```bash
# Check if nginx is running
sudo systemctl status nginx

# Start if not running
sudo systemctl start nginx

# Check port 443 is open
sudo netstat -tlnp | grep 443
```

### "Certificate error" in browser
This is normal for self-signed certs. Click through the warning.

### "Port already in use"
```bash
# Find what's using the port
sudo lsof -i :443

# Kill if needed
sudo kill -9 <PID>
```

### Voice features not working
1. Verify HTTPS is working: `https://YOUR_IP`
2. Run diagnostic tool: `https://YOUR_IP/static/voice-diagnostic.html`
3. Check browser console (F12) for errors
4. Verify microphone permissions
5. See [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING.md)

### Nginx not starting
```bash
# Check configuration
docker exec nora_nginx nginx -t

# View detailed logs
docker-compose logs nginx

# Common issues:
# - Certificate files missing
# - Port conflicts
# - Configuration syntax errors
```

---

## 📊 Expected Results

After completing all steps:

```
✅ Server accessible via HTTPS
✅ HTTP redirects to HTTPS
✅ SSL certificate valid (self-signed warning expected)
✅ Gateway responsive
✅ Microphone permissions allowed
✅ Voice input working (🎤 button active)
✅ Voice output working (AI speaks)
✅ All features fully functional
```

---

## 🎯 Next Steps

1. ✅ Complete deployment checklist
2. ✅ Test all features work
3. ✅ Create user accounts
4. ✅ Set up monitoring/backups
5. ✅ Document access information
6. ✅ Train users on features

---

## 📞 Additional Resources

- [Features Guide](../FEATURES.md) - Complete feature documentation
- [Voice Features](../features/VOICE.md) - Voice setup and configuration
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md) - Common issues and fixes
- [Nginx Documentation](https://nginx.org/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Docker Documentation](https://docs.docker.com/)

---

**Deployment Complete!** 🚀

For questions or issues, refer to the troubleshooting guide or check the diagnostic tool.
