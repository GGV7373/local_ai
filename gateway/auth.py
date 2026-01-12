"""
Nora AI - Authentication Module
"""
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import defaultdict

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from config import (
    SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD,
    TOKEN_EXPIRE_HOURS, RATE_LIMIT_WINDOW, MAX_LOGIN_ATTEMPTS
)

# Try to import bcrypt for better password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Rate limiting storage
login_attempts: Dict[str, List[float]] = defaultdict(list)


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
