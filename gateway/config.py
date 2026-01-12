"""
Nora AI - Configuration Module
"""
import os
import secrets
from pathlib import Path
from typing import Dict, Any, Set

# =============================================================================
# AI Configuration
# =============================================================================
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://ollama:11434")
AI_MODEL = os.getenv("AI_MODEL", "llama2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
