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
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

app = FastAPI(title="Nora AI")

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

# =============================================================================
# Authentication
# =============================================================================
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed

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

def load_company_context() -> str:
    """Load all text files from company_info folder as context."""
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
    
    return "\n".join(context_parts)

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
async def ask_ollama(message: str, context: str) -> str:
    """Query Ollama."""
    config = get_config()
    
    # Load custom system prompt if exists
    system_prompt_file = COMPANY_INFO_DIR / "system_prompt.txt"
    if system_prompt_file.exists():
        base_prompt = system_prompt_file.read_text()
    else:
        base_prompt = f"You are {config.get('assistant_name', 'Nora')}, an AI assistant for {config.get('company_name', 'the company')}."
    
    system_prompt = f"""{base_prompt}

Use this information to answer questions:
{context}

Be helpful, friendly, and concise. If asked about files or documents, refer to the information provided above."""

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{AI_SERVER_URL}/api/chat",
            json={
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

async def ask_gemini(message: str, context: str) -> str:
    """Query Google Gemini."""
    config = get_config()
    prompt = f"""You are {config.get('assistant_name', 'Nora')}, an AI assistant for {config.get('company_name', 'the company')}.

Use this information to answer questions:
{context}

User question: {message}

Be helpful, friendly, and concise."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def ask_ai(message: str) -> str:
    """Query the AI with company context."""
    context = load_company_context()
    
    if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
        return await ask_gemini(message, context)
    else:
        return await ask_ollama(message, context)

# =============================================================================
# Models
# =============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str

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
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/config")
async def config():
    return get_config()

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        token = create_token(request.username)
        return {
            "success": True,
            "token": token,
            "username": request.username,
            "expires_in": TOKEN_EXPIRE_HOURS * 3600
        }
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
    """Chat with the AI (requires authentication)."""
    try:
        response = await ask_ai(request.message)
        return {"response": response}
    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

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

# Mount static files
static_path = Path("/app/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
