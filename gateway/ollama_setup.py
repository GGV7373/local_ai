"""
Nora AI - Ollama Setup & Installation Module
"""
import os
import platform
import subprocess
import shutil
import logging
import asyncio
from typing import List

import httpx
from fastapi import HTTPException

from config import AI_SERVER_URL

logger = logging.getLogger(__name__)


def get_system_info() -> dict:
    """Get system information for setup guidance."""
    system = platform.system().lower()
    is_linux = system == "linux"
    is_mac = system == "darwin"
    is_windows = system == "windows"
    
    # Check if we're in Docker
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    # Check if Ollama is installed locally
    ollama_installed = shutil.which("ollama") is not None
    
    return {
        "system": system,
        "is_linux": is_linux,
        "is_mac": is_mac,
        "is_windows": is_windows,
        "in_docker": in_docker,
        "ollama_installed": ollama_installed,
        "can_auto_install": is_linux and not in_docker,
        "ai_server_url": AI_SERVER_URL
    }


async def check_ollama_connection() -> tuple:
    """Check if Ollama is running and get models."""
    ollama_running = False
    ollama_models = []
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                ollama_running = True
                ollama_models = [m["name"] for m in res.json().get("models", [])]
    except:
        pass
    
    return ollama_running, ollama_models


def install_ollama_linux() -> dict:
    """Install Ollama on Linux systems."""
    system = platform.system().lower()
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    if in_docker:
        raise HTTPException(
            status_code=400, 
            detail="Cannot install Ollama from inside Docker. Please install on the host machine."
        )
    
    if system != "linux":
        raise HTTPException(
            status_code=400, 
            detail=f"Auto-install only supported on Linux. Your system: {system}"
        )
    
    # Check if already installed
    if shutil.which("ollama"):
        return {"success": True, "message": "Ollama is already installed", "already_installed": True}
    
    try:
        logger.info("Starting Ollama installation...")
        
        # Download and run install script
        result = subprocess.run(
            ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Installation failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Installation failed: {result.stderr}")
        
        logger.info("Ollama installed successfully")
        return {
            "success": True, 
            "message": "Ollama installed successfully!",
            "output": result.stdout[-500:] if result.stdout else ""
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Installation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Installation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def start_ollama_service() -> dict:
    """Start Ollama service on Linux."""
    system = platform.system().lower()
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    if in_docker:
        raise HTTPException(status_code=400, detail="Cannot start Ollama from inside Docker")
    
    if not shutil.which("ollama"):
        raise HTTPException(status_code=400, detail="Ollama is not installed")
    
    try:
        # Start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait a bit for it to start
        await asyncio.sleep(2)
        
        # Check if it's running
        running, _ = await check_ollama_connection()
        if running:
            return {"success": True, "message": "Ollama started successfully"}
        
        return {"success": True, "message": "Ollama start command sent. It may take a moment to be ready."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def pull_ollama_model(model: str) -> dict:
    """Pull an Ollama model."""
    # Check if Ollama is accessible
    running, _ = await check_ollama_connection()
    if not running:
        raise HTTPException(status_code=503, detail="Ollama is not running")
    
    try:
        logger.info(f"Pulling model: {model}")
        
        # Use Ollama API to pull model
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for large models
            response = await client.post(
                f"{AI_SERVER_URL}/api/pull",
                json={"name": model, "stream": False}
            )
            
            if response.status_code == 200:
                return {"success": True, "message": f"Model '{model}' pulled successfully!"}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model pull timed out. Large models may take longer.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pull error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def list_ollama_models() -> dict:
    """List available Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                models = res.json().get("models", [])
                return {"success": True, "models": [m["name"] for m in models]}
            return {"success": False, "models": [], "error": "Ollama not responding"}
    except:
        return {"success": False, "models": [], "error": "Cannot connect to Ollama"}
