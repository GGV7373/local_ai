"""
Nora AI - Pydantic Models
"""
from typing import Optional, List
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    language: str = "en"
    provider: str = "ollama"
    use_fallback: bool = True


class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    size: int
    type: str
    modified: str


class FileUploadResponse(BaseModel):
    """File upload response model."""
    success: bool
    filename: str
    path: str
    message: str


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    provider: str
    language: str


class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    provider: str
    ollama_status: Optional[dict] = None
    gemini_available: bool = False


class OllamaInstallRequest(BaseModel):
    """Ollama installation request model."""
    action: str  # "install", "start", "pull_model"
    model: Optional[str] = None


class OllamaStatusResponse(BaseModel):
    """Ollama status response model."""
    installed: bool
    running: bool
    models: List[str] = []
    message: str = ""
