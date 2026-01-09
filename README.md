# Nora AI

Self-hosted AI assistant with secure authentication, file management, and document processing.

## ✨ Features

- 🔐 **Secure Login System** - JWT-based authentication
- 📁 **File Management** - Upload, view, download, and delete files
- 📄 **Document Processing** - Reads .docx, .pdf, .txt, .json, .xlsx, and more
- 🤖 **AI Context** - AI uses all your files to answer questions
- ☁️ **Cloudflare Tunnel** - Secure public access with IP detection
- 🎨 **Modern Web UI** - Responsive design with dark theme

## 🚀 Quick Start

```bash
chmod +x setup.sh
./setup.sh
```

The setup will:
1. Detect and display your public IP address
2. Configure company name, AI model, and admin credentials
3. Set up optional Cloudflare Tunnel
4. Start all services automatically

## 📁 File Structure

```
├── setup.sh              # Setup & deploy script
├── docker-compose.yml    # Container configuration
├── .env                  # Your settings (auto-generated)
├── company_info/         # Company files (AI reads these)
│   ├── config.json       # Company name, assistant name
│   ├── system_prompt.txt # Custom AI personality
│   ├── about.txt         # Company description
│   └── *.txt, *.md, ...  # Any documents
├── uploads/              # User-uploaded files (via web UI)
└── gateway/              # Web server
```

## 📄 Supported File Types

The AI can read content from:

| Type | Extensions |
|------|------------|
| Text | .txt, .md, .json, .csv, .xml, .yaml |
| Documents | .docx, .pdf, .rtf |
| Spreadsheets | .xlsx, .xls |
| Code | .py, .js, .ts, .java, .cpp, .html, .css |

## 🔐 Authentication

Default credentials (can be changed during setup):
- **Username:** `admin`
- **Password:** *(auto-generated or your choice)*

Credentials are stored in `.env` file.

## ☁️ Cloudflare Tunnel

For secure public access without opening ports:

1. Go to https://one.dash.cloudflare.com
2. Zero Trust → Networks → Tunnels → Create
3. Copy the tunnel token
4. Run `./setup.sh` and paste when prompted
5. In Cloudflare dashboard, configure:
   - **Service:** `http://gateway:8765`
   - **Access Policy:** Add your email or IP restrictions

The setup script shows your public IP - useful for Cloudflare Access policies.

## 🛠️ Commands

```bash
# Stop all services
docker compose down

# Start services
docker compose up -d

# Start with Cloudflare tunnel
docker compose --profile tunnel up -d

# View logs
docker compose logs -f

# View tunnel logs
docker logs nora_cloudflared -f

# Restart
docker compose restart

# Rebuild after code changes
docker compose build --no-cache gateway
docker compose up -d
```

## 🌐 Access

| Location | URL |
|----------|-----|
| Local | http://localhost:8765 |
| LAN | http://YOUR_IP:8765 |
| Public | Your Cloudflare tunnel URL |

## ⚙️ Environment Variables

The `.env` file contains:

```env
# AI Configuration
AI_MODEL=llama2
AI_PROVIDER=ollama

# Security
SECRET_KEY=your_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password

# Cloudflare (optional)
USE_CLOUDFLARE=true
CLOUDFLARE_TUNNEL_TOKEN=your_token
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login and get JWT token |
| `/auth/verify` | GET | Verify token validity |
| `/chat` | POST | Chat with AI (auth required) |
| `/files/list` | GET | List files |
| `/files/upload` | POST | Upload file |
| `/files/download/{dir}/{file}` | GET | Download file |
| `/files/view/{dir}/{file}` | GET | View file content |
| `/files/delete/{dir}/{file}` | DELETE | Delete file |
| `/files/stats` | GET | Get file statistics |

## 📦 Requirements

- Linux server with Docker
- 8GB+ RAM (for local AI with Ollama)
- Docker Compose
