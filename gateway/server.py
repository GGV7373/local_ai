"""
Audio Gateway Server

A stateless FastAPI server that:
- Receives text commands from desktop clients (via WebSocket or REST)
- Forwards text to the existing AI server API
- Returns AI text responses to clients

This gateway NEVER processes audio - it only handles text.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import httpx
import ollama
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    """Load gateway configuration from config.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    # Default configuration
    return {
        "gateway_host": "0.0.0.0",
        "gateway_port": 8765,
        "ai_server_url": "http://localhost:11434",
        "ai_model": "llama2",
        "max_response_length": 2000,
        "request_timeout": 60,
        "enable_websocket": True,
        "enable_rest": True,
        "log_level": "INFO"
    }


config = load_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("log_level", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gateway")

# FastAPI app
app = FastAPI(
    title="Audio Gateway",
    description="Stateless proxy between desktop clients and AI server",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class CommandRequest(BaseModel):
    """Request model for text commands."""
    text: str
    client_id: Optional[str] = None


class CommandResponse(BaseModel):
    """Response model for AI responses."""
    text: str
    success: bool
    timestamp: str
    client_id: Optional[str] = None


# ============================================================================
# AI Server Communication
# ============================================================================

async def query_ai_server(text: str) -> str:
    """
    Forward text to the existing AI server and return the response.
    
    This function communicates with the existing Ollama-based AI server.
    The AI server is treated as a black box - we only send text and receive text.
    """
    try:
        logger.info(f"Forwarding to AI server: {text[:100]}...")
        
        # Use the ollama library to communicate with the AI server
        response = await asyncio.to_thread(
            ollama.chat,
            model=config.get("ai_model", "llama2"),
            messages=[{"role": "user", "content": text}]
        )
        
        ai_response = response["message"]["content"].strip()
        
        # Truncate if needed
        max_length = config.get("max_response_length", 2000)
        if len(ai_response) > max_length:
            ai_response = ai_response[:max_length] + "..."
        
        logger.info(f"AI response received: {ai_response[:100]}...")
        return ai_response
        
    except Exception as e:
        logger.error(f"Error querying AI server: {e}")
        return f"I'm sorry, I couldn't process your request. Error: {str(e)}"


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Audio Gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "rest": "/api/command",
            "websocket": "/ws"
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
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """
    REST endpoint for processing text commands.
    
    Receives text from client, forwards to AI server, returns response.
    """
    if not config.get("enable_rest", True):
        raise HTTPException(status_code=503, detail="REST API is disabled")
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text command is required")
    
    logger.info(f"REST command from {request.client_id or 'unknown'}: {request.text[:50]}...")
    
    # Forward to AI server
    ai_response = await query_ai_server(request.text.strip())
    
    return CommandResponse(
        text=ai_response,
        success=True,
        timestamp=datetime.utcnow().isoformat(),
        client_id=request.client_id
    )


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


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with desktop clients.
    
    Protocol:
    - Client connects and sends: {"type": "connect", "client_id": "xxx"}
    - Client sends commands: {"type": "command", "text": "user command here"}
    - Server responds: {"type": "response", "text": "AI response", "success": true}
    """
    if not config.get("enable_websocket", True):
        await websocket.close(code=1013, reason="WebSocket is disabled")
        return
    
    client_id = None
    
    try:
        # Accept connection
        await websocket.accept()
        
        # Wait for initial handshake with client_id
        try:
            init_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            client_id = init_data.get("client_id", f"client_{id(websocket)}")
        except asyncio.TimeoutError:
            client_id = f"client_{id(websocket)}"
        
        manager.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to Audio Gateway",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "command")
            
            if msg_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                
            elif msg_type == "command":
                # Process text command
                text = data.get("text", "").strip()
                
                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty command received",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                logger.info(f"WebSocket command from {client_id}: {text[:50]}...")
                
                # Forward to AI server
                ai_response = await query_ai_server(text)
                
                # Send response back to client
                await websocket.send_json({
                    "type": "response",
                    "text": ai_response,
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif msg_type == "disconnect":
                # Client requested disconnect
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
    
    logger.info(f"Starting Audio Gateway on {host}:{port}")
    logger.info(f"AI Server: {config.get('ai_server_url')}")
    logger.info(f"AI Model: {config.get('ai_model')}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=config.get("log_level", "info").lower()
    )


if __name__ == "__main__":
    main()
