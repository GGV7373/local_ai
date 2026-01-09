# Local AI Assistant - Client-Server Audio Layer

A production-ready, scalable audio control layer that connects user microphones to an existing AI system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DESKTOP CLIENT (per user)                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────────┐ │
│  │   MIC   │──▶│  VOSK   │──▶│ WHISPER │──▶│  TEXT   │──▶│ Gateway Client│ │
│  │  Input  │   │  Wake   │   │   STT   │   │  Only   │   │   (HTTP/WS)   │ │
│  └─────────┘   │  Word   │   │(Offline)│   └─────────┘   └───────┬───────┘ │
│                └─────────┘   └─────────┘                         │         │
│                                                                   │         │
│  ┌─────────┐   ┌─────────┐                                       │         │
│  │ SPEAKER │◀──│ pyttsx3 │◀──────────────────────────────────────┘         │
│  │ Output  │   │   TTS   │        (AI response as TEXT)                    │
│  └─────────┘   │(Offline)│                                                 │
│                └─────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ TEXT ONLY (no audio)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUDIO GATEWAY (Ubuntu Server + Docker)                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐ │
│  │   FastAPI   │──▶│   Memory    │──▶│    Proxy    │──▶│  Ollama (LLM)   │ │
│  │  REST + WS  │   │ PostgreSQL  │   │  (Stateless)│   │   (unchanged)   │ │
│  │  + Web UI   │◀──│             │◀──│             │◀──│                 │ │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

### Desktop Client
- ✅ **Offline wake word detection** (VOSK)
- ✅ **Offline speech-to-text** (OpenAI Whisper)
- ✅ **Offline text-to-speech** (pyttsx3)
- ✅ **No cloud APIs** - everything runs locally
- ✅ **Text-only communication** with server

### Audio Gateway (Server)
- ✅ **Scalable** - Docker + Docker Compose
- ✅ **Conversation Memory** - PostgreSQL database
- ✅ **Web Interface** - Browser-based chat with voice
- ✅ **Multiple clients** - WebSocket + REST API
- ✅ **Context-aware AI** - Uses conversation history

### Web Interface
- ✅ **Real-time chat** via WebSocket
- ✅ **Voice input** (browser speech recognition)
- ✅ **Voice output** (browser text-to-speech)
- ✅ **Session management** - Multiple conversations
- ✅ **Mobile responsive**

---

## Quick Start (Ubuntu Server)

### Prerequisites

- Ubuntu 20.04+ server
- Docker & Docker Compose
- 4GB+ RAM (8GB recommended for LLM)

### 1. Clone and Deploy

```bash
# Clone or upload your project
cd /path/to/local_ai

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

This will:
- Install Docker if needed
- Start PostgreSQL, Redis, Ollama, and Gateway
- Pull the LLM model (llama2)

### 2. Access the Services

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | http://your-server:8765 | Browser chat interface |
| REST API | http://your-server:8765/api/command | API endpoint |
| WebSocket | ws://your-server:8765/ws | Real-time connection |
| Health | http://your-server:8765/health | Status check |

### 3. Connect Desktop Client

On user's Windows machine:

```powershell
# Update client config to point to server
# Edit client/config.json:
# "gateway_rest_url": "http://your-server:8765/api/command"

cd client
pip install -r requirements.txt
python main.py
```

## Configuration

### Gateway Configuration (`gateway/config.json`)

```json
{
    "gateway_host": "0.0.0.0",      // Listen on all interfaces
    "gateway_port": 8765,           // Server port
    "ai_server_url": "http://localhost:11434",  // Ollama API
    "ai_model": "llama2",           // LLM model to use
    "max_response_length": 2000,    // Truncate long responses
    "request_timeout": 60,          // API timeout in seconds
    "enable_websocket": true,       // Enable WebSocket endpoint
    "enable_rest": true,            // Enable REST endpoint
    "log_level": "INFO"             // Logging level
}
```

### Client Configuration (`client/config.json`)

```json
{
    "gateway_url": "ws://localhost:8765/ws",       // WebSocket endpoint
    "gateway_rest_url": "http://localhost:8765/api/command",  // REST endpoint
    "use_websocket": true,          // Use WebSocket (true) or REST (false)
    "wake_word": "hey nora",        // Wake word phrase
    "vosk_model_path": "../vosk_model",  // Path to VOSK model
    "whisper_model": "base",        // Whisper model size
    "command_duration": 5,          // Recording duration in seconds
    "sample_rate": 16000,           // Audio sample rate
    "greeting_message": "Hello boss, how can I help?",  // Greeting after wake word
    "tts_rate": 150,                // Speech rate
    "tts_volume": 1.0,              // Volume (0.0 - 1.0)
    "auto_reconnect": true,         // Auto-reconnect on disconnect
    "reconnect_delay": 5,           // Reconnect delay in seconds
    "client_id": null,              // Client ID (auto-generated if null)
    "log_level": "INFO"             // Logging level
}
```

## API Reference

### REST API

#### POST `/api/command`

Send a text command and receive an AI response.

**Request:**
```json
{
    "text": "What is the capital of France?",
    "client_id": "client123"
}
```

**Response:**
```json
{
    "text": "The capital of France is Paris.",
    "success": true,
    "timestamp": "2026-01-09T12:00:00.000000",
    "client_id": "client123"
}
```

#### GET `/health`

Check gateway health status.

### WebSocket API

Connect to `/ws` for real-time communication.

**Handshake:**
```json
{"type": "connect", "client_id": "client123"}
```

**Command:**
```json
{"type": "command", "text": "What is the capital of France?"}
```

**Response:**
```json
{
    "type": "response",
    "text": "The capital of France is Paris.",
    "success": true,
    "timestamp": "2026-01-09T12:00:00.000000"
}
```

## Example Flow

```
[Desktop Client]                    [Gateway]                   [AI Server]
      │                                 │                            │
      │ User says "Hey Nora"            │                            │
      │ ◄── Wake word detected          │                            │
      │                                 │                            │
      │ Speaks: "Hello boss..."         │                            │
      │                                 │                            │
      │ User speaks command             │                            │
      │ ◄── Records 5 seconds           │                            │
      │                                 │                            │
      │ Whisper transcribes             │                            │
      │ "What is the weather?"          │                            │
      │                                 │                            │
      │ ──── POST /api/command ────────▶│                            │
      │      {"text": "What is..."}     │                            │
      │                                 │ ──── ollama.chat() ───────▶│
      │                                 │                            │
      │                                 │ ◄─── AI response ──────────│
      │                                 │                            │
      │ ◄─── {"text": "The weather..."}─│                            │
      │                                 │                            │
      │ pyttsx3 speaks response         │                            │
      │                                 │                            │
```

## Folder Structure

```
local_ai/
├── docker-compose.yml          # Docker orchestration
├── deploy.sh                   # Ubuntu deployment script
├── .env.example                # Environment variables template
│
├── client/                     # Desktop client (runs on user machines)
│   ├── config.json             # Client configuration
│   ├── main.py                 # Main entry point
│   ├── wake_word.py            # VOSK wake word engine
│   ├── stt.py                  # Whisper STT engine
│   ├── tts.py                  # pyttsx3 TTS engine
│   ├── gateway_client.py       # Gateway communication
│   └── requirements.txt        # Client dependencies
│
├── gateway/                    # Audio gateway server (Docker)
│   ├── Dockerfile              # Container build file
│   ├── config.json             # Gateway configuration
│   ├── server.py               # Basic FastAPI server
│   ├── server_enhanced.py      # Enhanced server with memory
│   ├── database.py             # PostgreSQL models
│   ├── static/
│   │   └── index.html          # Web chat interface
│   └── requirements.txt        # Gateway dependencies
│
├── vosk_model/                 # VOSK model (pre-existing)
└── llm/                        # Existing LLM backend (unchanged)
```

---

## Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f gateway

# Stop all services
docker compose down

# Restart a service
docker compose restart gateway

# Rebuild after code changes
docker compose up -d --build

# Check service status
docker compose ps

# Pull latest LLM model
docker exec nora_ollama ollama pull llama2

# Access database
docker exec -it nora_db psql -U nora -d nora_db

# Shell into gateway container
docker exec -it nora_gateway /bin/bash
```

---

## Scaling

### Multiple Gateway Instances

```yaml
# In docker-compose.yml
gateway:
  deploy:
    replicas: 3
```

### Load Balancer (Nginx)

Uncomment the nginx service in `docker-compose.yml` for production deployments with SSL.

### GPU Support (for Ollama)

Uncomment the GPU section in `docker-compose.yml` if you have an NVIDIA GPU:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

---

## Troubleshooting

### "VOSK model not found"

Download a VOSK model from https://alphacephei.com/vosk/models and extract it to the `vosk_model` directory.

### "No microphone detected"

- Ensure `pyaudio` is installed correctly
- On Windows, you may need to install from a wheel: `pip install pyaudio`
- Check your microphone permissions in system settings

### "Gateway connection refused"

- Ensure the gateway is running: `python gateway/server.py`
- Check the port configuration matches between client and gateway
- Verify no firewall is blocking the connection

### "Ollama not responding"

- Ensure Ollama is running: `ollama serve`
- Pull a model if needed: `ollama pull llama2`
- Check the `ai_model` in gateway config matches an installed model

## Technology Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Wake Word | VOSK | Offline wake word detection |
| STT | OpenAI Whisper | Offline speech transcription |
| TTS | pyttsx3 | Offline speech synthesis |
| Gateway | FastAPI + Uvicorn | HTTP/WebSocket server |
| AI Server | Ollama | LLM inference (unchanged) |

## Design Principles

1. **Separation of Concerns**: Client handles audio, gateway handles text routing
2. **Stateless Gateway**: No session data, no audio processing, just proxying
3. **Offline Client**: All audio processing happens locally
4. **Text-Only Communication**: Only text crosses the network boundary
5. **Modular Design**: Each component can be replaced independently
