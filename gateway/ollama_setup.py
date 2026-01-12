"""
Nora AI - Ollama Setup & Installation Module
Linux Private Server Edition with GPU Detection
"""
import os
import platform
import subprocess
import shutil
import logging
import asyncio
from typing import List, Dict, Optional

import httpx
from fastapi import HTTPException

from config import AI_SERVER_URL

logger = logging.getLogger(__name__)


def get_system_info() -> dict:
    """Get system information for setup guidance (Linux-only)."""
    system = platform.system().lower()
    is_linux = system == "linux"
    
    # Check if we're in Docker
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    # Check if Ollama is installed locally
    ollama_installed = shutil.which("ollama") is not None
    
    # Check for GPU support
    gpu_info = detect_gpu()
    
    return {
        "system": system,
        "is_linux": is_linux,
        "in_docker": in_docker,
        "ollama_installed": ollama_installed,
        "can_auto_install": is_linux and not in_docker,
        "ai_server_url": AI_SERVER_URL,
        "gpu": gpu_info
    }


def detect_gpu() -> Dict:
    """Detect available GPU for Ollama acceleration."""
    gpu_info = {
        "available": False,
        "type": None,
        "name": None,
        "memory": None
    }
    
    # Check for NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            gpu_info["available"] = True
            gpu_info["type"] = "nvidia"
            gpu_info["name"] = parts[0].strip() if len(parts) > 0 else "Unknown"
            gpu_info["memory"] = f"{parts[1].strip()} MB" if len(parts) > 1 else None
            return gpu_info
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check for AMD GPU (ROCm)
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_info["available"] = True
            gpu_info["type"] = "amd"
            gpu_info["name"] = "AMD GPU (ROCm)"
            return gpu_info
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return gpu_info


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


async def delete_ollama_model(model: str) -> dict:
    """Delete an Ollama model."""
    running, models = await check_ollama_connection()
    if not running:
        raise HTTPException(status_code=503, detail="Ollama is not running")
    
    if model not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model}' not found")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{AI_SERVER_URL}/api/delete",
                json={"name": model}
            )
            
            if response.status_code == 200:
                return {"success": True, "message": f"Model '{model}' deleted successfully!"}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_ollama_model_info(model: str) -> dict:
    """Get detailed information about a specific model."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AI_SERVER_URL}/api/show",
                json={"name": model}
            )
            
            if response.status_code == 200:
                return {"success": True, "info": response.json()}
            else:
                return {"success": False, "error": f"Model not found: {model}"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_ollama_health() -> dict:
    """Get comprehensive Ollama health status."""
    health = {
        "running": False,
        "url": AI_SERVER_URL,
        "models": [],
        "model_count": 0,
        "gpu": detect_gpu()
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check API
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                health["running"] = True
                models = res.json().get("models", [])
                health["models"] = [
                    {
                        "name": m.get("name"),
                        "size": m.get("size"),
                        "modified_at": m.get("modified_at")
                    }
                    for m in models
                ]
                health["model_count"] = len(models)
    except Exception as e:
        health["error"] = str(e)
    
    return health


def configure_ollama_systemd() -> dict:
    """Configure Ollama as a systemd service with proper settings."""
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    if in_docker:
        raise HTTPException(status_code=400, detail="Cannot configure systemd from inside Docker")
    
    if platform.system().lower() != "linux":
        raise HTTPException(status_code=400, detail="Systemd configuration only available on Linux")
    
    # Create override directory and file
    override_dir = "/etc/systemd/system/ollama.service.d"
    override_file = f"{override_dir}/override.conf"
    
    override_content = """[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_ORIGINS=*"
"""
    
    try:
        # This would need sudo - return instructions instead
        return {
            "success": True,
            "instructions": [
                f"sudo mkdir -p {override_dir}",
                f"echo '{override_content}' | sudo tee {override_file}",
                "sudo systemctl daemon-reload",
                "sudo systemctl restart ollama"
            ],
            "override_content": override_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
