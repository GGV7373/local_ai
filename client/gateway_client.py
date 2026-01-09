"""
Gateway Client

Handles communication with the Audio Gateway server.
Supports both WebSocket and REST API connections.
"""

import asyncio
import json
import logging
import uuid
from typing import Callable, Optional

import httpx

logger = logging.getLogger("client.gateway")

# Try to import websockets, fall back to REST if not available
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets package not available, using REST API only")


class GatewayClient:
    """
    Client for communicating with the Audio Gateway server.
    
    Supports both WebSocket (for real-time) and REST API connections.
    """
    
    def __init__(
        self,
        gateway_url: str = "ws://localhost:8765/ws",
        rest_url: str = "http://localhost:8765/api/command",
        use_websocket: bool = True,
        client_id: Optional[str] = None,
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0
    ):
        """
        Initialize the gateway client.
        
        Args:
            gateway_url: WebSocket URL for the gateway
            rest_url: REST API URL for the gateway
            use_websocket: Whether to use WebSocket (True) or REST (False)
            client_id: Unique client identifier
            auto_reconnect: Whether to automatically reconnect on disconnect
            reconnect_delay: Delay between reconnection attempts
        """
        self.gateway_url = gateway_url
        self.rest_url = rest_url
        self.use_websocket = use_websocket and WEBSOCKETS_AVAILABLE
        self.client_id = client_id or str(uuid.uuid4())[:8]
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        
        self.websocket = None
        self.connected = False
        self._response_callback: Optional[Callable[[str], None]] = None
    
    async def connect(self):
        """Connect to the gateway (WebSocket mode)."""
        if not self.use_websocket:
            logger.info("Using REST API mode")
            self.connected = True
            return
        
        try:
            logger.info(f"Connecting to gateway: {self.gateway_url}")
            self.websocket = await websockets.connect(self.gateway_url)
            
            # Send handshake
            await self.websocket.send(json.dumps({
                "type": "connect",
                "client_id": self.client_id
            }))
            
            # Wait for welcome message
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "connected":
                self.connected = True
                logger.info(f"Connected to gateway as {self.client_id}")
            else:
                logger.warning(f"Unexpected response: {data}")
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from the gateway."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"type": "disconnect"}))
                await self.websocket.close()
            except Exception:
                pass
            finally:
                self.websocket = None
        
        self.connected = False
        logger.info("Disconnected from gateway")
    
    async def send_command(self, text: str) -> str:
        """
        Send a text command to the gateway and get the AI response.
        
        Args:
            text: The text command to send
            
        Returns:
            The AI response text
        """
        if self.use_websocket:
            return await self._send_websocket(text)
        else:
            return await self._send_rest(text)
    
    async def _send_websocket(self, text: str) -> str:
        """Send command via WebSocket."""
        if not self.connected or not self.websocket:
            await self.connect()
        
        try:
            # Send command
            await self.websocket.send(json.dumps({
                "type": "command",
                "text": text
            }))
            
            # Wait for response
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "response" and data.get("success"):
                return data.get("text", "")
            elif data.get("type") == "error":
                logger.error(f"Gateway error: {data.get('message')}")
                return f"Error: {data.get('message', 'Unknown error')}"
            else:
                logger.warning(f"Unexpected response: {data}")
                return ""
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connected = False
            
            if self.auto_reconnect:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                return await self.send_command(text)
            
            raise
    
    async def _send_rest(self, text: str) -> str:
        """Send command via REST API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rest_url,
                    json={
                        "text": text,
                        "client_id": self.client_id
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("text", "")
                else:
                    logger.error(f"REST error: {response.status_code}")
                    return f"Error: HTTP {response.status_code}"
                    
        except Exception as e:
            logger.error(f"REST error: {e}")
            return f"Error: {str(e)}"
    
    def send_command_sync(self, text: str) -> str:
        """
        Synchronous wrapper for send_command.
        
        Args:
            text: The text command to send
            
        Returns:
            The AI response text
        """
        return asyncio.get_event_loop().run_until_complete(self.send_command(text))


class SyncGatewayClient:
    """
    Synchronous gateway client for simpler integration.
    Uses REST API only for maximum compatibility.
    """
    
    def __init__(
        self,
        rest_url: str = "http://localhost:8765/api/command",
        client_id: Optional[str] = None
    ):
        """
        Initialize the synchronous gateway client.
        
        Args:
            rest_url: REST API URL for the gateway
            client_id: Unique client identifier
        """
        self.rest_url = rest_url
        self.client_id = client_id or str(uuid.uuid4())[:8]
    
    def send_command(self, text: str) -> str:
        """
        Send a text command to the gateway and get the AI response.
        
        Args:
            text: The text command to send
            
        Returns:
            The AI response text
        """
        import requests
        
        try:
            response = requests.post(
                self.rest_url,
                json={
                    "text": text,
                    "client_id": self.client_id
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("text", "")
            else:
                logger.error(f"REST error: {response.status_code}")
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"REST error: {e}")
            return f"Error: {str(e)}"


if __name__ == "__main__":
    # Test the gateway client
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        client = GatewayClient(use_websocket=False)
        response = await client.send_command("Hello, what is the capital of France?")
        print(f"Response: {response}")
    
    asyncio.run(test())
