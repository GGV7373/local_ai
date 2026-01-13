# Nora AI - Linux Private Server Edition

Self-hosted AI assistant for private networks. No cloud dependencies, direct IP access only.

##  Features

-  **Linux Only** - Optimized for Linux servers
-  **Secure Login** - JWT-based authentication
-  **File Management** - Upload, view, download, delete files
-  **Document Processing** - Reads .docx, .pdf, .txt, .xlsx, and more
-  **Multi-Provider AI** - Ollama (local) + Gemini 2.x (cloud)
-  **Streaming Responses** - Real-time AI output
-  **GPU Support** - NVIDIA & AMD GPU detection
-  **Private Network** - Access via local IP only

##  Quick Start

```bash
chmod +x setup.sh
./setup.sh
```

The setup will:
1. Check for Linux environment
2. Detect and configure GPU (if available)
3. Install or configure Ollama
4. Set up admin credentials
5. Configure firewall (optional)
6. Start all services

##  AI Providers

### Ollama (Local - Recommended)
- Runs locally, no API keys needed
- GPU acceleration for NVIDIA/AMD
- Models: llama3.2, mistral, gemma2, codellama

### Google Gemini (Cloud)
- Requires API key from https://aistudio.google.com
- Models: gemini-2.0-flash, gemini-2.5-flash, gemini-1.5-pro
- Streaming support

##  File Structure

```
 setup.sh              # Linux setup script
 docker-compose.yml    # Container configuration
 .env                  # Your settings (auto-generated)
 company_info/         # Company files (AI reads these)
    config.json       # Company/assistant name
    system_prompt.txt # Custom AI personality
    *.txt, *.md, ...  # Any documents
 uploads/              # User-uploaded files
 nginx/                # Optional SSL reverse proxy
 gateway/              # Web server
```

##  Supported File Types

| Type | Extensions |
|------|------------|
| Text | .txt, .md, .json, .csv, .xml, .yaml |
| Documents | .docx, .pdf, .rtf |
| Spreadsheets | .xlsx, .xls |
| Code | .py, .js, .ts, .java, .cpp, .html, .css |

##  Authentication

Default credentials (configurable during setup):
- **Username:** `admin`
- **Password:** *(auto-generated or custom)*

Stored in `.env` file.

##  Commands

```bash
# Stop all services
docker compose down

# Start services (native Ollama)
docker compose up -d gateway

# Start with Docker Ollama
docker compose --profile docker-ollama up -d

# View logs
docker compose logs -f gateway

# Restart
docker compose restart

# Rebuild after code changes
docker compose build --no-cache gateway
docker compose up -d
```

##  API Endpoints

### Chat
- `POST /chat` - Send message, get response
- `POST /chat/stream` - Stream response via SSE

### Ollama Management
- `GET /ollama/health` - Ollama status & GPU info
- `GET /ollama/models` - List installed models
- `POST /ollama/pull/{model}` - Download model
- `DELETE /ollama/models/{model}` - Remove model

### Files
- `GET /files/list` - List files
- `POST /files/upload` - Upload file
- `GET /files/download/{dir}/{file}` - Download
- `DELETE /files/delete/{dir}/{file}` - Delete

##  Firewall

The setup script can configure UFW or firewalld:

```bash
# Manual UFW
sudo ufw allow 8765/tcp comment "Nora AI"

# Manual firewalld
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --reload
```

##  GPU Support

### NVIDIA
Requires nvidia-docker or Docker with NVIDIA Container Toolkit:
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### AMD (ROCm)
Requires ROCm drivers and Docker with AMD GPU support.

##  Native Ollama (Recommended)

For best performance, run Ollama natively instead of in Docker:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure for network access
sudo mkdir -p /etc/systemd/system/ollama.service.d/
echo '[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_ORIGINS=*"' | sudo tee /etc/systemd/system/ollama.service.d/override.conf

# Restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Pull a model
ollama pull llama3.2
```

##  Documentation

Complete guides for all features and deployment:

### Getting Started
- [Quick Start Guide](docs/getting-started/QUICKSTART.md) - Get running in 3 steps
- [Complete Features Guide](docs/FEATURES.md) - All features and capabilities

### Features
- [Voice Features](docs/features/VOICE.md) - Voice input/output setup and configuration
- [Audio & Export](docs/features/AUDIO_EXPORT.md) - Audio transcription and chat export

### Deployment
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Complete deployment with HTTPS

### Troubleshooting
- [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING.md) - Common issues and solutions

---

##  License

MIT License
