"""
Nora AI - Document Processing Module
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Document processing libraries (graceful fallback)
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from config import COMPANY_INFO_DIR, cache

logger = logging.getLogger(__name__)


def extract_text_from_file(filepath: str) -> str:
    """Extract text content from various file types."""
    ext = Path(filepath).suffix.lower()
    
    try:
        # Plain text files
        if ext in ['.txt', '.md', '.json', '.log', '.csv', '.xml', '.html', '.htm']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        # Word documents
        if ext == '.docx' and DOCX_AVAILABLE:
            doc = Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
        
        # PDF files
        if ext == '.pdf' and PDF_AVAILABLE:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text() or '')
                return '\n'.join(text)
        
        # Fallback: try to read as text
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return f"[Binary file: {Path(filepath).name}]"
            
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {e}")
        return f"[Error reading file: {str(e)}]"


def load_company_context() -> str:
    """Load all company context from the company_info directory."""
    cache_key = 'company_context'
    
    # Check cache
    if cache_key in cache['data'] and cache['timestamps'].get(cache_key, 0) > 0:
        import time
        if time.time() - cache['timestamps'][cache_key] < cache['ttl']:
            return cache['data'][cache_key]
    
    context_parts = []
    
    if COMPANY_INFO_DIR.exists():
        for file_path in sorted(COMPANY_INFO_DIR.rglob('*')):
            if file_path.is_file():
                content = extract_text_from_file(str(file_path))
                if content and not content.startswith('[Binary') and not content.startswith('[Error'):
                    relative_path = file_path.relative_to(COMPANY_INFO_DIR)
                    context_parts.append(f"=== {relative_path} ===\n{content}")
    
    context = '\n\n'.join(context_parts)
    
    # Cache the result
    import time
    cache['data'][cache_key] = context
    cache['timestamps'][cache_key] = time.time()
    
    return context


def get_config() -> Dict[str, Any]:
    """Get configuration from config.json."""
    config_path = COMPANY_INFO_DIR / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config.json: {e}")
    return {}


def get_system_prompt() -> str:
    """Get the system prompt from file or return default."""
    prompt_path = COMPANY_INFO_DIR / 'system_prompt.txt'
    if prompt_path.exists():
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading system_prompt.txt: {e}")
    
    return """You are Nora, a helpful AI assistant. You help users with their questions 
and tasks. Be friendly, professional, and helpful. If you have company context available, 
use it to provide more relevant answers."""


def save_uploaded_file(filename: str, content: bytes, subdir: Optional[str] = None) -> str:
    """Save an uploaded file to the company_info directory."""
    if subdir:
        target_dir = COMPANY_INFO_DIR / subdir
    else:
        target_dir = COMPANY_INFO_DIR
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / filename
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Invalidate cache
    if 'company_context' in cache['data']:
        del cache['data']['company_context']
        if 'company_context' in cache['timestamps']:
            del cache['timestamps']['company_context']
    
    return str(file_path)
