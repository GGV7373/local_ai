# Quick Start Guide

Get Nora AI up and running in 3 simple steps.

---

## Prerequisites

Before you begin, ensure you have:
- Linux server (Ubuntu/Debian/CentOS)
- Docker installed
- Docker Compose installed
- Server IP address

Check if Docker is installed:
```bash
docker --version
docker-compose --version
```

---

## 🚀 3-Step Setup

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

**What you'll see:**
```
🔒 Nora AI - HTTPS Certificate Setup
=====================================

✓ OpenSSL found
✓ Docker found
✓ Docker Compose found

Enter your server IP address (optional, press Enter to skip): 192.168.1.100

Generating SSL certificates...
✓ SSL directory created
✓ Certificates generated successfully
✓ Permissions set

Next steps:
1. Start services: docker-compose up -d
2. Access: https://192.168.1.100:443
```

### Step 2: Start Services

```bash
# Using Docker Compose
docker-compose up -d
```

**What you'll see:**
```
Creating network "local_ai_nora_network" ... done
Creating local_ai_gateway_1 ... done
Creating nora_nginx ... done
```

**Verify services are running:**
```bash
docker-compose ps
```

Should show all containers as "Up".

### Step 3: Access & Test

Open your browser and navigate to:
```
https://YOUR_SERVER_IP:443
```

Examples:
- `https://192.168.1.100:443`
- `https://10.0.0.50:443`

**What to expect:**
1. Browser shows SSL warning (normal for self-signed certificates)
2. Click "Advanced" → "Proceed to site"
3. Login page loads
4. Enter your credentials
5. Start chatting!

**Test voice features:**
1. Click 🎤 microphone button
2. Allow microphone access when prompted
3. Speak: "Hello"
4. Voice input should work!

---

## 🎯 Next Steps

Now that Nora AI is running:

### Configure Your Assistant
1. Go to **Files** tab
2. Upload company documents
3. Configure system prompts in `company_info/system_prompt.txt`

### Test Features
- ✅ Voice Input (🎤 button)
- ✅ Voice Output (AI speaks responses)
- ✅ Audio Transcription (Files tab)
- ✅ Chat Export (💾 Save button)
- ✅ Document Upload

### Troubleshooting
If something doesn't work:
- Run diagnostic: `https://YOUR_IP/static/voice-diagnostic.html`
- Check [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING.md)
- Review [Deployment Guide](../deployment/DEPLOYMENT.md) for details

---

## 📋 Common Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart gateway
docker-compose restart nginx

# Check status
docker-compose ps
```

### Testing
```bash
# Test HTTPS connection
curl -k https://localhost:443

# Test backend
curl http://localhost:8765/health

# View nginx logs
docker-compose logs nginx
```

---

## 🆘 Quick Troubleshooting

### "Connection refused"
```bash
# Check if services are running
docker-compose ps

# Start if not running
docker-compose up -d
```

### "Certificate error"
This is normal for self-signed certificates. Click "Advanced" → "Proceed".

### Voice not working
1. Verify HTTPS is working (voice requires HTTPS)
2. Allow microphone permissions
3. Try different browser (Chrome/Edge recommended)
4. Run diagnostic tool

### Port already in use
```bash
# Find what's using port 443
sudo lsof -i :443

# Kill process or change port in docker-compose.yml
```

---

## 🔐 Security Notes

### Self-Signed Certificates
- Browser will show ⚠️ warning (this is normal)
- Click "Advanced" → "Proceed" to continue
- Voice features work despite the warning
- Certificates valid for 365 days

### For Production
Upgrade to Let's Encrypt for trusted certificates:
```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

Then update `nginx/nginx.conf` with the certificate paths.

---

## 📚 Additional Resources

### Getting Started
- [Features Guide](../FEATURES.md) - Complete feature list
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Detailed deployment
- [Voice Features](../features/VOICE.md) - Voice configuration
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md) - Common issues

### Configuration
- `company_info/config.json` - Company settings
- `company_info/system_prompt.txt` - AI behavior
- `docker-compose.yml` - Service configuration
- `nginx/nginx.conf` - Web server settings

---

## 🎉 You're All Set!

Nora AI is now running and ready to use. Key features:

- 🤖 **AI Chat** - Ask questions, get help
- 🎤 **Voice Input** - Speak your questions
- 🔊 **Voice Output** - AI speaks back
- 🎵 **Audio Transcription** - Upload audio files
- 📁 **Document Upload** - Add company knowledge
- 💾 **Chat Export** - Save conversations
- 🔐 **Secure HTTPS** - Encrypted connections

**Have questions?** Check the [Features Guide](../FEATURES.md) or [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md).

---

**Happy chatting!** 🚀
