"""
Nora AI - Configuration Module
Linux Private Server Edition
"""
import os
import secrets
from pathlib import Path
from typing import Dict, Any, Set

# =============================================================================
# AI Configuration
# =============================================================================
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:11434")
AI_MODEL = os.getenv("AI_MODEL", "llama3.2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Available Gemini models (2.x series)
GEMINI_MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# =============================================================================
# Security Configuration
# =============================================================================
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_EXPIRE_HOURS = 24
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 5

# =============================================================================
# Server Configuration
# =============================================================================
SERVER_IP = os.getenv("SERVER_IP", "")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8765"))

# =============================================================================
# Paths
# =============================================================================
COMPANY_INFO_DIR = Path("/app/company_info")
UPLOADS_DIR = Path("/app/uploads")
STATIC_DIR = Path("/app/static")

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Allowed file extensions for upload
# =============================================================================
ALLOWED_EXTENSIONS: Set[str] = {
    '.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml',
    '.doc', '.docx', '.pdf', '.rtf',
    '.xls', '.xlsx',
    '.html', '.htm',
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.css'
}

# =============================================================================
# Cache Configuration
# =============================================================================
CONTEXT_CACHE_TTL = 60  # Cache context for 60 seconds

# Cache storage
cache: Dict[str, Any] = {
    "data": {},
    "timestamps": {},
    "ttl": CONTEXT_CACHE_TTL
}

# =============================================================================
# Streaming Configuration
# =============================================================================
STREAM_CHUNK_SIZE = 1024  # bytes for streaming responses
