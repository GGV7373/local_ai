"""
Audio Gateway Server (Enhanced)

A scalable FastAPI server that:
- Receives text commands from desktop clients and web UI
- Forwards text to the existing AI server API with conversation context
- Stores conversation history in PostgreSQL
- Supports multiple clients via WebSocket and REST
- Serves a web interface for browser-based chat
- Supports multiple AI providers (Ollama, Gemini)
- Exports transcripts to downloadable text files

This gateway NEVER processes audio - it only handles text.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel

# Database imports
try:
    from database import MemoryStore, async_session
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# AI Provider imports
try:
    from ai_providers import get_ai_provider, AIProvider
    AI_PROVIDERS_AVAILABLE = True
except ImportError:
    AI_PROVIDERS_AVAILABLE = False

# Transcript imports
try:
    from transcript import format_transcript, format_notes
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
COMPANY_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "company_info", "config.json")


def load_config():
    """Load gateway configuration from config.json."""
    config = {}
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    
    # Default configuration (can be overridden by environment variables)
    defaults = {
        "gateway_host": os.getenv("GATEWAY_HOST", "0.0.0.0"),
        "gateway_port": int(os.getenv("GATEWAY_PORT", "8765")),
        "ai_server_url": os.getenv("AI_SERVER_URL", "http://ollama:11434"),
        "ai_model": os.getenv("AI_MODEL", "llama2"),
        "ai_provider": os.getenv("AI_PROVIDER", "auto"),  # auto, ollama, gemini
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-pro"),
        "max_response_length": int(os.getenv("MAX_RESPONSE_LENGTH", "2000")),
        "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "60")),
        "enable_websocket": True,
        "enable_rest": True,
        "enable_memory": os.getenv("ENABLE_MEMORY", "true").lower() == "true",
        "memory_context_length": int(os.getenv("MEMORY_CONTEXT_LENGTH", "10")),
        "log_level": os.getenv("LOG_LEVEL", "INFO")
    }
    
    # Merge defaults with loaded config
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    return config


def load_company_config():
    """Load company configuration."""
    if os.path.exists(COMPANY_CONFIG_PATH):
        with open(COMPANY_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "company_name": "AI Assistant",
        "assistant_name": "Nora",
        "greeting": "Hello! How can I help you?"
    }


config = load_config()
company_config = load_company_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("log_level", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gateway")

# Initialize AI provider
ai_provider = None


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    global ai_provider
    
    # Startup
    logger.info("Starting Audio Gateway...")
    
    # Initialize AI provider
    if AI_PROVIDERS_AVAILABLE:
        try:
            ai_provider = get_ai_provider(config)
            logger.info(f"AI provider initialized: {type(ai_provider).__name__}")
        except Exception as e:
            logger.warning(f"AI provider initialization failed: {e}")
            logger.info("Falling back to direct Ollama")
    
    if DB_AVAILABLE and config.get("enable_memory", True):
        try:
            await MemoryStore.init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.warning("Running without conversation memory")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Audio Gateway...")


# FastAPI app
app = FastAPI(
    title="Nora Audio Gateway",
    description="Scalable gateway between clients and AI server with conversation memory",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ============================================================================
# Request/Response Models
# ============================================================================

class CommandRequest(BaseModel):
    """Request model for text commands."""
    text: str
    client_id: Optional[str] = None
    session_id: Optional[str] = None


class CommandResponse(BaseModel):
    """Response model for AI responses."""
    text: str
    success: bool
    timestamp: str
    client_id: Optional[str] = None
    session_id: Optional[str] = None


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    client_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response with conversation details."""
    session_id: str
    title: Optional[str]
    created_at: str


# ============================================================================
# AI Server Communication
# ============================================================================

async def query_ai_server(text: str, context: Optional[List[dict]] = None) -> str:
    """
    Forward text to the AI provider and return the response.
    
    Args:
        text: The user's message
        context: Optional conversation history for context
    """
    global ai_provider
    
    try:
        logger.info(f"Forwarding to AI: {text[:100]}...")
        
        # Use AI provider if available
        if ai_provider:
            ai_response = await ai_provider.generate(text, context)
        else:
            # Fallback to direct Ollama
            import ollama
            
            messages = []
            messages.append({
                "role": "system",
                "content": f"You are {company_config.get('assistant_name', 'Nora')}, a helpful AI assistant for {company_config.get('company_name', 'the company')}. Be concise and helpful."
            })
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": text})
            
            response = await asyncio.to_thread(
                ollama.chat,
                model=config.get("ai_model", "llama2"),
                messages=messages
            )
            
            ai_response = response["message"]["content"].strip()
        
        # Truncate if needed
        max_length = config.get("max_response_length", 2000)
        if len(ai_response) > max_length:
            ai_response = ai_response[:max_length] + "..."
        
        logger.info(f"AI response received: {ai_response[:100]}...")
        return ai_response
        
    except Exception as e:
        logger.error(f"Error querying AI: {e}")
        return f"I'm sorry, I couldn't process your request. Error: {str(e)}"


async def process_with_memory(
    text: str, 
    client_id: str, 
    session_id: Optional[str] = None
) -> tuple[str, str]:
    """
    Process a command with conversation memory.
    
    Returns:
        Tuple of (ai_response, session_id)
    """
    context = None
    
    # If memory is enabled and database is available
    if DB_AVAILABLE and config.get("enable_memory", True):
        try:
            # Create session if not provided
            if not session_id:
                session_id = str(uuid.uuid4())[:8]
                await MemoryStore.create_conversation(
                    client_id=client_id,
                    session_id=session_id,
                    title=text[:50] + "..." if len(text) > 50 else text
                )
            
            # Get conversation history for context
            context_length = config.get("memory_context_length", 10)
            context = await MemoryStore.get_conversation_history(session_id, limit=context_length)
            
            # Store user message
            await MemoryStore.add_message(session_id, "user", text)
            
        except Exception as e:
            logger.warning(f"Memory operation failed: {e}")
            session_id = session_id or str(uuid.uuid4())[:8]
    else:
        session_id = session_id or str(uuid.uuid4())[:8]
    
    # Query AI with context
    ai_response = await query_ai_server(text, context)
    
    # Store assistant response
    if DB_AVAILABLE and config.get("enable_memory", True):
        try:
            await MemoryStore.add_message(session_id, "assistant", ai_response)
        except Exception as e:
            logger.warning(f"Failed to store response: {e}")
    
    return ai_response, session_id


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Serve web UI or return API info."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {
        "status": "online",
        "service": "Nora Audio Gateway",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "rest": "/api/command",
            "websocket": "/ws",
            "web_ui": "/static/index.html",
            "conversations": "/api/conversations"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "ai_server_url": config.get("ai_server_url"),
        "ai_model": config.get("ai_model"),
        "websocket_enabled": config.get("enable_websocket", True),
        "rest_enabled": config.get("enable_rest", True),
        "memory_enabled": DB_AVAILABLE and config.get("enable_memory", True),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """
    REST endpoint for processing text commands.
    
    Receives text from client, forwards to AI server with context, returns response.
    """
    if not config.get("enable_rest", True):
        raise HTTPException(status_code=503, detail="REST API is disabled")
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text command is required")
    
    client_id = request.client_id or "anonymous"
    logger.info(f"REST command from {client_id}: {request.text[:50]}...")
    
    # Process with memory
    ai_response, session_id = await process_with_memory(
        request.text.strip(),
        client_id,
        request.session_id
    )
    
    return CommandResponse(
        text=ai_response,
        success=True,
        timestamp=datetime.utcnow().isoformat(),
        client_id=client_id,
        session_id=session_id
    )


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreate):
    """Create a new conversation session."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    session_id = str(uuid.uuid4())[:8]
    
    try:
        await MemoryStore.create_conversation(
            client_id=request.client_id,
            session_id=session_id,
            title=request.title
        )
        
        return ConversationResponse(
            session_id=session_id,
            title=request.title,
            created_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{client_id}")
async def get_conversations(client_id: str):
    """Get all conversations for a client."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        conversations = await MemoryStore.get_user_conversations(client_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{client_id}/{session_id}/messages")
async def get_messages(client_id: str, session_id: str, limit: int = 50):
    """Get messages from a conversation."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        messages = await MemoryStore.get_conversation_history(session_id, limit=limit)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Transcript Export Endpoints
# ============================================================================

@app.get("/api/conversations/{client_id}/{session_id}/export")
async def export_transcript(
    client_id: str, 
    session_id: str, 
    format: str = "txt"
):
    """
    Export conversation as downloadable text file.
    
    Args:
        format: 'txt' for plain text, 'notes' for condensed notes, 'json' for raw data
    """
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        messages = await MemoryStore.get_conversation_history(session_id, limit=1000)
        
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if format == "json":
            return {
                "session_id": session_id,
                "client_id": client_id,
                "exported_at": datetime.utcnow().isoformat(),
                "messages": messages
            }
        
        elif format == "notes":
            if TRANSCRIPT_AVAILABLE:
                content = format_notes(
                    messages,
                    title=f"Conversation {session_id}"
                )
            else:
                content = "\n".join([
                    f"{'Q' if m['role']=='user' else 'A'}: {m['content']}" 
                    for m in messages
                ])
            
            return PlainTextResponse(
                content=content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=notes_{session_id}.txt"
                }
            )
        
        else:  # txt format
            if TRANSCRIPT_AVAILABLE:
                content = format_transcript(
                    messages,
                    company_name=company_config.get("company_name", "AI Assistant"),
                    assistant_name=company_config.get("assistant_name", "Nora"),
                    session_id=session_id
                )
            else:
                # Simple fallback format
                lines = [f"Conversation Transcript - {session_id}", "=" * 40, ""]
                for msg in messages:
                    role = "You" if msg["role"] == "user" else company_config.get("assistant_name", "AI")
                    lines.append(f"{role}: {msg['content']}")
                    lines.append("")
                content = "\n".join(lines)
            
            return PlainTextResponse(
                content=content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=transcript_{session_id}.txt"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/company")
async def get_company_info():
    """Get company configuration for UI customization."""
    return company_config


# ============================================================================
# WebSocket Endpoint
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections from multiple clients."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected: {client_id} (total: {len(self.active_connections)})")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id} (total: {len(self.active_connections)})")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    
    Protocol:
    - Client connects and sends: {"type": "connect", "client_id": "xxx"}
    - Client sends commands: {"type": "command", "text": "...", "session_id": "xxx"}
    - Server responds: {"type": "response", "text": "...", "session_id": "xxx"}
    """
    if not config.get("enable_websocket", True):
        await websocket.close(code=1013, reason="WebSocket is disabled")
        return
    
    client_id = None
    session_id = None
    
    try:
        await websocket.accept()
        
        # Wait for initial handshake
        try:
            init_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            client_id = init_data.get("client_id", f"client_{id(websocket)}")
            session_id = init_data.get("session_id")
        except asyncio.TimeoutError:
            client_id = f"client_{id(websocket)}"
        
        manager.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Create new session if needed
        if not session_id and DB_AVAILABLE and config.get("enable_memory", True):
            session_id = str(uuid.uuid4())[:8]
            try:
                await MemoryStore.create_conversation(client_id, session_id)
            except Exception as e:
                logger.warning(f"Failed to create session: {e}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "session_id": session_id,
            "message": "Connected to Nora Gateway",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Main message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "command")
            
            if msg_type == "ping":
                await websocket.send_json({
                    "type": "pong", 
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif msg_type == "command":
                text = data.get("text", "").strip()
                msg_session_id = data.get("session_id", session_id)
                
                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty command received"
                    })
                    continue
                
                logger.info(f"WebSocket command from {client_id}: {text[:50]}...")
                
                # Process with memory
                ai_response, msg_session_id = await process_with_memory(
                    text, client_id, msg_session_id
                )
                
                # Update session_id if new
                if not session_id:
                    session_id = msg_session_id
                
                await websocket.send_json({
                    "type": "response",
                    "text": ai_response,
                    "success": True,
                    "session_id": msg_session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif msg_type == "new_session":
                # Start a new conversation
                session_id = str(uuid.uuid4())[:8]
                if DB_AVAILABLE and config.get("enable_memory", True):
                    try:
                        await MemoryStore.create_conversation(client_id, session_id)
                    except Exception as e:
                        logger.warning(f"Failed to create session: {e}")
                
                await websocket.send_json({
                    "type": "session_created",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif msg_type == "disconnect":
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        if client_id:
            manager.disconnect(client_id)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the gateway server."""
    import uvicorn
    
    host = config.get("gateway_host", "0.0.0.0")
    port = config.get("gateway_port", 8765)
    
    logger.info(f"Starting Nora Gateway on {host}:{port}")
    logger.info(f"AI Server: {config.get('ai_server_url')}")
    logger.info(f"AI Model: {config.get('ai_model')}")
    logger.info(f"Memory enabled: {DB_AVAILABLE and config.get('enable_memory', True)}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=config.get("log_level", "info").lower()
    )


if __name__ == "__main__":
    main()
