# Linux HTTPS Setup Guide for Nora AI

## 🔒 Enable HTTPS on Your Linux Server

Your Nora AI application is currently running on **HTTP**, which blocks voice features when accessed remotely. This guide shows how to set up **HTTPS** so voice input works from any network.

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

## 🚀 Step 1: Generate SSL Certificates

Run the provided script to generate self-signed certificates:

```bash
cd /path/to/local_ai/nginx
bash generate-ssl.sh
```

This creates:
- `ssl/cert.pem` - Certificate
- `ssl/key.pem` - Private key

The certificates are valid for 365 days and work with:
- localhost
- nora.local
- 127.0.0.1
- Any IP address (added to certificate)

---

## 🔧 Step 2: Update Docker Compose (If Using Docker)

If deploying with Docker, update `docker-compose.yml` to include nginx:

```yaml
services:
  # ... existing services ...
  
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
```

---

## 🌐 Step 3: Access Your Server

After setup, access via:

```
https://YOUR_SERVER_IP:443
```

Examples:
- `https://192.168.1.100:443`
- `https://10.0.0.50:443`
- `https://your-domain.com:443` (if using domain)

---

## ⚙️ Step 4: Configure Your Server IP

The default certificate is set for generic use. For best results with your specific IP:

### Option A: Regenerate with Your IP

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

### Option B: Use Generic Certificate

The default works fine. Browsers will show a warning, but voice features will work.

---

## 🚀 Step 5: Start Services

### If using Docker Compose:

```bash
cd /path/to/local_ai

# Start with SSL profile
docker-compose --profile ssl up -d

# Or without profile (if nginx is always enabled)
docker-compose up -d
```

### If running natively:

Start nginx separately:
```bash
# On Ubuntu/Debian
sudo nginx -c /path/to/local_ai/nginx/nginx.conf

# On CentOS/RHEL
sudo systemctl start nginx

# Verify it's running
sudo systemctl status nginx
```

---

## 🔍 Step 6: Verify HTTPS is Working

Check if HTTPS is accessible:

```bash
# Test HTTPS connection
curl -k https://localhost:443

# Test with your IP
curl -k https://192.168.1.100:443

# Check nginx is running
sudo systemctl status nginx
```

---

## 🎤 Step 7: Test Voice Feature

1. Open browser and go to: `https://YOUR_SERVER_IP:443`
2. Login to Nora AI
3. Click 🎤 microphone button
4. Speak something
5. Voice should work now!

---

## 🔐 Security Notes

### Self-Signed Certificates
- Browsers will show ⚠️ warning
- This is normal for self-signed certs
- Click "Advanced" → "Proceed" to continue
- Voice features work despite warning

### For Production (Optional)
Use Let's Encrypt for trusted certificates:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate free certificate
sudo certbot certonly --standalone -d your-domain.com

# Update nginx.conf to use these:
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
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
# Find what's using port 443
sudo lsof -i :443

# Kill if needed
sudo kill -9 <PID>
```

### Voice still not working
1. Verify HTTPS is working: `https://YOUR_IP`
2. Run diagnostic tool: `https://YOUR_IP/static/voice-diagnostic.html`
3. Check browser console (F12) for errors
4. Verify microphone permissions

---

## 📝 Quick Commands Reference

```bash
# Generate certificates
bash /path/to/nginx/generate-ssl.sh

# Check nginx config
sudo nginx -t

# Start nginx
sudo systemctl start nginx

# Stop nginx
sudo systemctl stop nginx

# Restart nginx (apply changes)
sudo systemctl restart nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log

# Test HTTPS
curl -k https://localhost

# Check if port 443 is open
sudo netstat -tlnp | grep 443
```

---

## 🔄 Update Certificate

Certificates expire after 365 days. Regenerate them:

```bash
# Remove old certificates
rm -rf /path/to/nginx/ssl/*

# Regenerate
bash /path/to/nginx/generate-ssl.sh

# Restart nginx
sudo systemctl restart nginx
```

---

## 📊 Expected Result

After setup:
- ✅ HTTPS accessible: `https://YOUR_IP:443`
- ✅ HTTP redirects to HTTPS
- ✅ Voice input works (🎤 button functional)
- ✅ Voice output works (AI speaks)
- ✅ Audio transcription works
- ✅ All features available

---

## 🎯 Next Steps

1. Generate SSL certificates: `bash generate-ssl.sh`
2. Configure nginx with your IP (optional)
3. Start services: `docker-compose up -d`
4. Access: `https://YOUR_SERVER_IP:443`
5. Test voice feature
6. Enjoy! 🎉

---

## 📞 Still Having Issues?

Check:
1. ✅ Certificates generated: `ls nginx/ssl/`
2. ✅ Nginx running: `sudo systemctl status nginx`
3. ✅ Port 443 accessible: `curl -k https://localhost`
4. ✅ Microphone permissions allowed
5. ✅ Browser allows HTTPS (accept self-signed cert warning)

---

**Last Updated:** January 12, 2026

For more help, see:
- `VOICE_TROUBLESHOOTING.md` - General voice issues
- `NETWORK_ERROR_FIX.md` - Network-specific fixes
- Nginx docs: https://nginx.org/
