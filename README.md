# Nora AI - Self-Hosted AI Assistant

A self-hosted AI assistant with web chat interface, conversation memory, and secure access via Cloudflare Tunnel.

## Features

- 🤖 **Local AI** - Runs Ollama with llama2 (or any model)
- 🌐 **Web Chat** - Browser-based chat interface
- 💾 **Memory** - PostgreSQL-backed conversation history
- 🔒 **Secure Access** - Cloudflare Tunnel (no open ports) or SSL
- 🎨 **Customizable** - Company branding support
- 📝 **Transcripts** - Export conversations to text
- 🔑 **Multi-Provider** - Ollama (local) or Google Gemini (cloud)

## Quick Start

### Prerequisites

- Linux server (any distro: Debian, Ubuntu, Fedora, Arch, Gentoo, Alpine, etc.)
- Docker and Docker Compose installed
- 8GB+ RAM recommended

### Deploy

```bash
# Clone or upload files to your server
cd /path/to/nora-ai

# Make scripts executable
chmod +x *.sh

# Run interactive setup wizard
./setup.sh

# Deploy
./deploy.sh
```

Access the web UI at `http://your-server:8765`

## Setup Wizard

The interactive `setup.sh` script configures everything:

### 1. Company Information
- Company name and assistant name
- Custom greeting message
- Brand colors
- System prompt (AI personality)

### 2. AI Provider
- **Ollama** - Local, free, private (default)
- **Google Gemini** - Cloud-based, requires API key
- **Both** - Gemini primary with Ollama fallback

### 3. Database
- PostgreSQL database name
- Username and auto-generated secure password
- All stored in `.env`

### 4. Secure Access
- **Local only** - http://localhost:8765
- **Cloudflare Tunnel** - Secure public access, no open ports
- **Custom Domain + SSL** - Let's Encrypt certificates

## Cloudflare Tunnel (Recommended)

Secure access without opening firewall ports - configured via `./setup.sh`:

### Setup Steps

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Navigate to **Networks → Tunnels → Create a tunnel**
3. Name your tunnel (e.g., "nora-ai")
4. Copy the token (the long string)
5. Run `./setup.sh` and select option **2) Cloudflare Tunnel**
6. Paste your token when prompted
7. In Cloudflare, configure:
   - **Public hostname:** `ai.yourdomain.com`
   - **Service:** `http://gateway:8765`

### Manual Setup (Alternative)

Just add to your `.env`:
```bash
USE_CLOUDFLARE=true
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiN2I2NDQ0...your-token-here
```

Then run: `sudo docker compose --profile tunnel up -d`

**Benefits:**
- 🔒 No open ports needed
- 🔐 Free automatic SSL
- 🛡️ DDoS protection included
- 🌐 Works behind NAT/firewalls

## Configuration Files

After running `setup.sh`:

| File | Purpose |
|------|---------|
| `.env` | All environment variables |
| `company_info/config.json` | Company branding |
| `company_info/system_prompt.txt` | AI personality |

### Manual Configuration

Copy and edit `.env.example`:

```bash
cp .env.example .env
nano .env
```

Key settings:
- `AI_MODEL` - Ollama model (llama2, mistral, llama3)
- `AI_PROVIDER` - auto, ollama, or gemini
- `GEMINI_API_KEY` - Google Gemini API key
- `USE_CLOUDFLARE` - Enable Cloudflare Tunnel
- `CLOUDFLARE_TUNNEL_TOKEN` - Your tunnel token

## Directory Structure

```
├── setup.sh            # Interactive setup wizard
├── deploy.sh           # Deployment script
├── update.sh           # Update script
├── setup_ssl.sh        # SSL certificate setup
├── setup_git.sh        # Git repository setup
├── docker-compose.yml  # Container orchestration
├── .env.example        # Environment template
├── gateway/            # API server
│   ├── server_enhanced.py
│   ├── database.py
│   ├── ai_providers.py
│   ├── transcript.py
│   ├── static/
│   ├── Dockerfile
│   └── requirements.txt
├── company_info/       # Your branding
│   ├── config.json
│   └── system_prompt.txt
└── nginx/              # Reverse proxy (SSL)
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8765 | API + Web UI |
| Ollama | 11434 | LLM server |
| Postgres | 5433 | Database |
| Redis | 6380 | Cache |
| Cloudflared | - | Tunnel (optional) |
| Nginx | 443 | SSL proxy (optional) |

## Commands

```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop everything
docker compose down

# Pull different AI model
docker exec nora_ollama ollama pull mistral

# Update to latest version
./update.sh
```

## Updating

```bash
./update.sh
```

This preserves your `.env` and `company_info/` settings.

## Supported Distros

Scripts are distro-neutral and work on:
- Debian / Ubuntu
- Fedora / CentOS / RHEL
- Arch Linux
- Gentoo
- Alpine Linux
- Any Linux with Docker

## License

MIT
