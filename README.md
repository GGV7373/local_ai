# Nora AI - Self-Hosted AI Assistant

A self-hosted AI assistant with web chat interface, conversation memory, and optional SSL support.

## Features

- 🤖 **Local AI** - Runs Ollama with llama2 (or any model)
- 🌐 **Web Chat** - Browser-based chat interface
- 💾 **Memory** - PostgreSQL-backed conversation history
- 🔒 **SSL Ready** - Let's Encrypt integration
- 🎨 **Customizable** - Company branding support
- 📝 **Transcripts** - Export conversations to text

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

# Deploy (downloads AI model automatically)
./deploy.sh
```

Access the web UI at `http://your-server:8765`

## Configuration

### Environment Variables

Copy and edit `.env.example`:

```bash
cp .env.example .env
nano .env
```

Key settings:
- `AI_MODEL` - Ollama model (default: llama2)
- `AI_PROVIDER` - auto, ollama, or gemini
- `GEMINI_API_KEY` - Optional Google Gemini API key

### Company Branding

Edit `company_info/config.json`:

```json
{
  "company_name": "Your Company",
  "assistant_name": "Nora",
  "greeting": "Hello! How can I help you today?"
}
```

Add a custom system prompt in `company_info/system_prompt.txt`.

## SSL Setup (Optional)

For HTTPS with a custom domain:

```bash
# Add to .env
DOMAIN=ai.yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Run SSL setup
./setup_ssl.sh
```

## Updating

```bash
./update.sh
```

This preserves your `.env` and `company_info/` settings.

## Directory Structure

```
├── deploy.sh           # Main deployment script
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
│   ├── static/         # Web UI files
│   ├── Dockerfile
│   └── requirements.txt
├── company_info/       # Your branding
│   ├── config.json
│   └── system_prompt.txt
├── nginx/              # Reverse proxy (SSL)
│   └── nginx.conf.template
└── transcripts/        # Exported conversations
```

## Services

| Service  | Port  | Description |
|----------|-------|-------------|
| Gateway  | 8765  | API + Web UI |
| Ollama   | 11434 | LLM server |
| Postgres | 5433  | Database |
| Redis    | 6380  | Cache |
| Nginx    | 443   | SSL proxy (optional) |

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
```

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
