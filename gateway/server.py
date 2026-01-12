"""
Nora AI - Advanced Gateway Server
With Authentication, File Management, and Document Processing
"""
import os
import json
import hashlib
import secrets
import httpx
import mimetypes
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import wraps, lru_cache
from collections import defaultdict
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Form, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt

# Try to import bcrypt for better password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nora AI", docs_url="/api/docs", redoc_url="/api/redoc")

# CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Configuration
# =============================================================================
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://ollama:11434")
AI_MODEL = os.getenv("AI_MODEL", "llama2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_EXPIRE_HOURS = 24

# Paths
COMPANY_INFO_DIR = Path("/app/company_info")
UPLOADS_DIR = Path("/app/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml',
    '.doc', '.docx', '.pdf', '.rtf',
    '.xls', '.xlsx',
    '.html', '.htm',
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.css'
}

# Security
security = HTTPBearer(auto_error=False)

# Rate limiting storage
login_attempts: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 5

# Context cache
_context_cache: Dict[str, Any] = {"content": None, "timestamp": 0}
CONTEXT_CACHE_TTL = 60  # Cache context for 60 seconds

# =============================================================================
# Authentication
# =============================================================================
def hash_password(password: str) -> str:
    """Hash a password using bcrypt if available, otherwise SHA-256."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, stored: str) -> bool:
    """Verify a password against stored hash."""
    # For plain text comparison (from env vars)
    if password == stored:
        return True
    # For bcrypt hashed passwords
    if BCRYPT_AVAILABLE and stored.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode(), stored.encode())
        except:
            pass
    # Fallback to SHA-256 comparison
    return hashlib.sha256(password.encode()).hexdigest() == stored

def check_rate_limit(ip: str) -> bool:
    """Check if IP is rate limited. Returns True if allowed."""
    now = time.time()
    # Clean old attempts
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    return len(login_attempts[ip]) < MAX_LOGIN_ATTEMPTS

def record_login_attempt(ip: str):
    """Record a failed login attempt."""
    login_attempts[ip].append(time.time())

def create_token(username: str) -> str:
    """Create a JWT token."""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get the current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = verify_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return username

# =============================================================================
# Document Processing
# =============================================================================
def extract_text_from_file(file_path: Path) -> str:
    """Extract text content from various file types."""
    suffix = file_path.suffix.lower()
    
    try:
        # Plain text files
        if suffix in {'.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml', 
                      '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.css', '.html', '.htm'}:
            return file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Word documents
        elif suffix == '.docx':
            try:
                from docx import Document
                doc = Document(str(file_path))
                return '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                return f"[DOCX file - install python-docx to read: {file_path.name}]"
            except Exception as e:
                return f"[Error reading DOCX: {str(e)}]"
        
        # PDF files
        elif suffix == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = []
                    for page in reader.pages:
                        text.append(page.extract_text() or '')
                    return '\n'.join(text)
            except ImportError:
                return f"[PDF file - install PyPDF2 to read: {file_path.name}]"
            except Exception as e:
                return f"[Error reading PDF: {str(e)}]"
        
        # RTF files
        elif suffix == '.rtf':
            try:
                from striprtf.striprtf import rtf_to_text
                return rtf_to_text(file_path.read_text(encoding='utf-8', errors='ignore'))
            except ImportError:
                return f"[RTF file - install striprtf to read: {file_path.name}]"
            except Exception as e:
                return f"[Error reading RTF: {str(e)}]"
        
        # Excel files
        elif suffix in {'.xls', '.xlsx'}:
            try:
                import pandas as pd
                df = pd.read_excel(str(file_path))
                return df.to_string()
            except ImportError:
                return f"[Excel file - install pandas openpyxl to read: {file_path.name}]"
            except Exception as e:
                return f"[Error reading Excel: {str(e)}]"
        
        else:
            return f"[Unsupported file type: {suffix}]"
            
    except Exception as e:
        return f"[Error reading file {file_path.name}: {str(e)}]"

def load_company_context(force_refresh: bool = False) -> str:
    """Load all text files from company_info folder as context. Uses caching."""
    global _context_cache
    
    now = time.time()
    if not force_refresh and _context_cache["content"] and (now - _context_cache["timestamp"]) < CONTEXT_CACHE_TTL:
        return _context_cache["content"]
    
    logger.info("Reloading document context...")
    context_parts = []
    
    # Load from company_info directory
    if COMPANY_INFO_DIR.exists():
        config_file = COMPANY_INFO_DIR / "config.json"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
                context_parts.append(f"Company: {config.get('company_name', 'Unknown')}")
                context_parts.append(f"Assistant Name: {config.get('assistant_name', 'Nora')}")
            except:
                pass
        
        # Load all files from company_info
        for file_path in COMPANY_INFO_DIR.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                try:
                    content = extract_text_from_file(file_path)
                    if content and not content.startswith('['):
                        context_parts.append(f"\n--- {file_path.name} ---\n{content}")
                except:
                    pass
    
    # Load from uploads directory
    if UPLOADS_DIR.exists():
        for file_path in UPLOADS_DIR.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                try:
                    content = extract_text_from_file(file_path)
                    if content and not content.startswith('['):
                        context_parts.append(f"\n--- Uploaded: {file_path.name} ---\n{content}")
                except:
                    pass
    
    result = "\n".join(context_parts)
    _context_cache["content"] = result
    _context_cache["timestamp"] = time.time()
    logger.info(f"Context loaded: {len(result)} characters from {len(context_parts)} sources")
    return result

def get_config() -> dict:
    """Load company config."""
    config_file = COMPANY_INFO_DIR / "config.json"
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except:
            pass
    return {"company_name": "My Company", "assistant_name": "Nora"}

# =============================================================================
# AI Providers
# =============================================================================
async def ask_ollama(message: str, context: str, model: str = None, language: str = "en") -> str:
    """Query Ollama with retry logic and better error handling."""
    config = get_config()
    
    # Load custom system prompt if exists
    system_prompt_file = COMPANY_INFO_DIR / "system_prompt.txt"
    if system_prompt_file.exists():
        base_prompt = system_prompt_file.read_text()
    else:
        base_prompt = f"You are {config.get('assistant_name', 'Nora')}, an AI assistant for {config.get('company_name', 'the company')}."
    
    # Add language instruction
    lang_instruction = ""
    if language == "no":
        lang_instruction = "\n\nIMPORTANT: Always respond in Norwegian (Norsk). The user prefers Norwegian language."
    elif language == "en":
        lang_instruction = "\n\nRespond in English."
    
    system_prompt = f"""{base_prompt}{lang_instruction}

Use this information to answer questions:
{context}

Be helpful, friendly, and concise. If asked about files or documents, refer to the information provided above."""

    use_model = model or AI_MODEL
    
    # Try with retries
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # First check if Ollama is running
                try:
                    health_check = await client.get(f"{AI_SERVER_URL}/api/tags", timeout=5.0)
                    if health_check.status_code != 200:
                        raise ConnectionError("Ollama is not responding")
                except httpx.ConnectError:
                    raise ConnectionError(
                        "Failed to connect to Ollama. Please check that:\n"
                        "1. Ollama is installed (https://ollama.com/download)\n"
                        "2. Ollama is running (run 'ollama serve' in terminal)\n"
                        "3. The AI_SERVER_URL is correct in your configuration"
                    )
                
                response = await client.post(
                    f"{AI_SERVER_URL}/api/chat",
                    json={
                        "model": use_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        "stream": False
                    }
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except httpx.ConnectError as e:
            last_error = ConnectionError(
                "Failed to connect to Ollama. Please check that:\n"
                "1. Ollama is installed (https://ollama.com/download)\n"
                "2. Ollama is running (run 'ollama serve' in terminal)\n"
                "3. The AI_SERVER_URL is correct in your configuration"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                last_error = ValueError(f"Model '{use_model}' not found. Please run: ollama pull {use_model}")
            else:
                last_error = e
        except Exception as e:
            last_error = e
        
        if attempt < max_retries - 1:
            await asyncio.sleep(1)  # Wait before retry
    
    raise last_error or Exception("Failed to connect to Ollama after multiple attempts")

async def ask_gemini(message: str, context: str, model: str = None, language: str = "en") -> str:
    """Query Google Gemini."""
    config = get_config()
    use_model = model or AI_MODEL or "gemini-1.5-flash"
    
    # Add language instruction
    lang_instruction = ""
    if language == "no":
        lang_instruction = "\n\nIMPORTANT: Always respond in Norwegian (Norsk). The user prefers Norwegian language."
    elif language == "en":
        lang_instruction = "\nRespond in English."
    
    prompt = f"""You are {config.get('assistant_name', 'Nora')}, an AI assistant for {config.get('company_name', 'the company')}.{lang_instruction}

Use this information to answer questions:
{context}

User question: {message}

Be helpful, friendly, and concise."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1/models/{use_model}:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def ask_ai(message: str, provider: str = None, model: str = None, language: str = "en") -> str:
    """Query the AI with company context. Supports dynamic provider switching."""
    context = load_company_context()
    
    # Use specified provider or fall back to default
    use_provider = provider or AI_PROVIDER
    
    try:
        if use_provider == "gemini" and GEMINI_API_KEY:
            return await ask_gemini(message, context, model, language)
        else:
            return await ask_ollama(message, context, model, language)
    except ConnectionError as e:
        # Try to fall back to Gemini if Ollama fails and Gemini is available
        if use_provider == "ollama" and GEMINI_API_KEY:
            logger.warning("Ollama unavailable, falling back to Gemini")
            return await ask_gemini(message, context, model, language) + "\n\n*(Note: Using Gemini as Ollama is currently unavailable)*"
        raise

# =============================================================================
# Models
# =============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None  # Optional: "ollama" or "gemini"
    model: Optional[str] = None  # Optional: override model
    language: Optional[str] = "en"  # Optional: "en" for English, "no" for Norwegian

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: str
    type: str
    readable: bool

# =============================================================================
# Public Routes (No Auth Required)
# =============================================================================
@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("/app/static/index.html")

@app.get("/health")
async def health():
    """Health check with Ollama status."""
    ollama_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                ollama_status = "connected"
                models = res.json().get("models", [])
                ollama_status = f"connected ({len(models)} models)"
    except:
        ollama_status = "disconnected"
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "ollama_status": ollama_status
    }

@app.get("/config")
async def config():
    return get_config()

@app.get("/providers")
async def get_providers():
    """Get available AI providers and their status."""
    providers = []
    
    # Check Ollama
    ollama_status = "unavailable"
    ollama_models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                ollama_status = "available"
                ollama_models = [m["name"] for m in res.json().get("models", [])]
    except:
        pass
    
    providers.append({
        "id": "ollama",
        "name": "Ollama (Local)",
        "status": ollama_status,
        "models": ollama_models,
        "default_model": AI_MODEL if AI_PROVIDER == "ollama" else "llama2"
    })
    
    # Check Gemini
    gemini_status = "available" if GEMINI_API_KEY else "not_configured"
    providers.append({
        "id": "gemini",
        "name": "Google Gemini",
        "status": gemini_status,
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"] if GEMINI_API_KEY else [],
        "default_model": AI_MODEL if AI_PROVIDER == "gemini" else "gemini-1.5-flash"
    })
    
    return {
        "providers": providers,
        "default_provider": AI_PROVIDER,
        "default_model": AI_MODEL
    }

@app.post("/auth/login")
async def login(request: LoginRequest, req: Request):
    """Authenticate user and return JWT token."""
    client_ip = req.client.host if req.client else "unknown"
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429, 
            detail="Too many login attempts. Please try again in 5 minutes."
        )
    
    if request.username == ADMIN_USERNAME and verify_password(request.password, ADMIN_PASSWORD):
        logger.info(f"Successful login for user: {request.username} from IP: {client_ip}")
        token = create_token(request.username)
        return {
            "success": True,
            "token": token,
            "username": request.username,
            "expires_in": TOKEN_EXPIRE_HOURS * 3600
        }
    
    # Record failed attempt
    record_login_attempt(client_ip)
    logger.warning(f"Failed login attempt for user: {request.username} from IP: {client_ip}")
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/auth/verify")
async def verify_auth(user: str = Depends(get_current_user)):
    """Verify if the current token is valid."""
    return {"valid": True, "username": user}

# =============================================================================
# Protected Routes (Auth Required)
# =============================================================================
@app.post("/chat")
async def chat(request: ChatRequest, user: str = Depends(get_current_user)):
    """Chat with the AI (requires authentication). Supports provider switching."""
    try:
        response = await ask_ai(request.message, request.provider, request.model, request.language)
        return {
            "response": response,
            "provider": request.provider or AI_PROVIDER,
            "model": request.model or AI_MODEL,
            "success": True
        }
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        error_msg = str(e)
        if "ollama" in error_msg.lower():
            return {
                "response": f"❌ **Connection Error**\n\n{error_msg}\n\n**Quick Fix:**\n1. Open a terminal\n2. Run: `ollama serve`\n3. Try again\n\nOr switch to Gemini if you have an API key configured.",
                "success": False,
                "error_type": "connection"
            }
        return {"response": f"Sorry, I couldn't connect: {error_msg}", "success": False}
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return {"response": f"⚠️ **Configuration Error**\n\n{str(e)}", "success": False, "error_type": "config"}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": f"Sorry, I encountered an error: {str(e)}", "success": False}

@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket chat endpoint."""
    await websocket.accept()
    
    # First message should be the auth token
    try:
        auth_msg = await websocket.receive_text()
        auth_data = json.loads(auth_msg)
        token = auth_data.get("token", "")
        
        if not verify_token(token):
            await websocket.send_text(json.dumps({"error": "Authentication required"}))
            await websocket.close()
            return
        
        await websocket.send_text(json.dumps({"authenticated": True}))
        
        while True:
            message = await websocket.receive_text()
            try:
                response = await ask_ai(message)
                await websocket.send_text(response)
            except Exception as e:
                await websocket.send_text(f"Sorry, I encountered an error: {str(e)}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass

# =============================================================================
# File Management Routes
# =============================================================================
@app.get("/files/list")
async def list_files(
    directory: str = Query("uploads", description="Directory to list: 'uploads' or 'company_info'"),
    user: str = Depends(get_current_user)
) -> List[FileInfo]:
    """List all files in the specified directory."""
    if directory == "company_info":
        base_dir = COMPANY_INFO_DIR
    else:
        base_dir = UPLOADS_DIR
    
    if not base_dir.exists():
        return []
    
    files = []
    for file_path in sorted(base_dir.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(base_dir)
            suffix = file_path.suffix.lower()
            
            files.append(FileInfo(
                name=file_path.name,
                path=str(rel_path),
                size=file_path.stat().st_size,
                modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                type=suffix[1:] if suffix else "unknown",
                readable=suffix in ALLOWED_EXTENSIONS
            ))
    
    return files

@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    directory: str = Form("uploads"),
    user: str = Depends(get_current_user)
):
    """Upload a file to the server."""
    # Validate file extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {suffix} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Choose directory
    if directory == "company_info":
        base_dir = COMPANY_INFO_DIR
    else:
        base_dir = UPLOADS_DIR
    
    # Ensure directory exists
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = base_dir / file.filename
    
    # Avoid overwriting - add number if exists
    counter = 1
    original_stem = file_path.stem
    while file_path.exists():
        file_path = base_dir / f"{original_stem}_{counter}{suffix}"
        counter += 1
    
    content = await file.read()
    file_path.write_bytes(content)
    
    return {
        "success": True,
        "filename": file_path.name,
        "size": len(content),
        "path": str(file_path.relative_to(base_dir))
    }

@app.get("/files/download/{directory}/{filename:path}")
async def download_file(
    directory: str,
    filename: str,
    user: str = Depends(get_current_user)
):
    """Download a file from the server."""
    if directory == "company_info":
        base_dir = COMPANY_INFO_DIR
    else:
        base_dir = UPLOADS_DIR
    
    file_path = base_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: ensure file is within the base directory
    try:
        file_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    )

@app.get("/files/view/{directory}/{filename:path}")
async def view_file(
    directory: str,
    filename: str,
    user: str = Depends(get_current_user)
):
    """View file content (text extraction for AI-readable content)."""
    if directory == "company_info":
        base_dir = COMPANY_INFO_DIR
    else:
        base_dir = UPLOADS_DIR
    
    file_path = base_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: ensure file is within the base directory
    try:
        file_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    content = extract_text_from_file(file_path)
    
    return {
        "filename": file_path.name,
        "content": content,
        "size": file_path.stat().st_size,
        "type": file_path.suffix[1:] if file_path.suffix else "unknown"
    }

@app.delete("/files/delete/{directory}/{filename:path}")
async def delete_file(
    directory: str,
    filename: str,
    user: str = Depends(get_current_user)
):
    """Delete a file from the server."""
    if directory == "company_info":
        base_dir = COMPANY_INFO_DIR
    else:
        base_dir = UPLOADS_DIR
    
    file_path = base_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: ensure file is within the base directory
    try:
        file_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent deleting config.json
    if file_path.name == "config.json" and directory == "company_info":
        raise HTTPException(status_code=403, detail="Cannot delete config.json")
    
    file_path.unlink()
    
    return {"success": True, "deleted": filename}

@app.get("/files/stats")
async def file_stats(user: str = Depends(get_current_user)):
    """Get statistics about files available to the AI."""
    stats = {
        "company_info": {"count": 0, "total_size": 0, "types": {}},
        "uploads": {"count": 0, "total_size": 0, "types": {}},
        "ai_readable_files": 0,
        "total_context_chars": 0
    }
    
    for directory, base_dir in [("company_info", COMPANY_INFO_DIR), ("uploads", UPLOADS_DIR)]:
        if base_dir.exists():
            for file_path in base_dir.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    size = file_path.stat().st_size
                    
                    stats[directory]["count"] += 1
                    stats[directory]["total_size"] += size
                    stats[directory]["types"][suffix] = stats[directory]["types"].get(suffix, 0) + 1
                    
                    if suffix in ALLOWED_EXTENSIONS:
                        stats["ai_readable_files"] += 1
    
    # Calculate context size
    context = load_company_context()
    stats["total_context_chars"] = len(context)
    
    return stats

# =============================================================================
# Ollama Setup & Installation Routes
# =============================================================================
import platform
import subprocess
import shutil

@app.get("/system/info")
async def system_info():
    """Get system information for setup guidance."""
    system = platform.system().lower()
    is_linux = system == "linux"
    is_mac = system == "darwin"
    is_windows = system == "windows"
    
    # Check if we're in Docker
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    
    # Check if Ollama is installed locally
    ollama_installed = shutil.which("ollama") is not None
    
    # Check Ollama connection
    ollama_running = False
    ollama_models = []
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code == 200:
                ollama_running = True
                ollama_models = [m["name"] for m in res.json().get("models", [])]
    except:
        pass
    
    return {
        "system": system,
        "is_linux": is_linux,
        "is_mac": is_mac,
        "is_windows": is_windows,
        "in_docker": in_docker,
        "ollama_installed": ollama_installed,
        "ollama_running": ollama_running,
        "ollama_models": ollama_models,
        "can_auto_install": is_linux and not in_docker,
        "ai_server_url": AI_SERVER_URL
    }

@app.post("/ollama/install")
async def install_ollama(user: str = Depends(get_current_user)):
    """Install Ollama on Linux systems. Only works on native Linux (not Docker)."""
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
    except Exception as e:
        logger.error(f"Installation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ollama/start")
async def start_ollama(user: str = Depends(get_current_user)):
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
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{AI_SERVER_URL}/api/tags")
                if res.status_code == 200:
                    return {"success": True, "message": "Ollama started successfully"}
        except:
            pass
        
        return {"success": True, "message": "Ollama start command sent. It may take a moment to be ready."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ollama/pull/{model}")
async def pull_model(model: str, user: str = Depends(get_current_user)):
    """Pull an Ollama model."""
    # Check if Ollama is accessible
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AI_SERVER_URL}/api/tags")
            if res.status_code != 200:
                raise HTTPException(status_code=503, detail="Ollama is not running")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama")
    
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
    except Exception as e:
        logger.error(f"Pull error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ollama/models")
async def list_models():
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

# Mount static files
static_path = Path("/app/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
