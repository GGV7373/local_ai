"""
AI Providers - Support for multiple AI backends

Supports:
- Ollama (local, free)
- Google Gemini (API key required)
"""

import asyncio
import json
import logging
import os
from typing import Optional, List

logger = logging.getLogger("gateway.ai")

# Try to import providers
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not available")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini not available - install with: pip install google-generativeai")


class AIProvider:
    """Base class for AI providers."""
    
    def __init__(self, config: dict):
        self.config = config
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from company_info."""
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "company_info", 
            "system_prompt.txt"
        )
        
        company_config_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "company_info", 
            "config.json"
        )
        
        # Load company config for substitutions
        company_config = {}
        if os.path.exists(company_config_path):
            with open(company_config_path, "r") as f:
                company_config = json.load(f)
        
        # Load and process system prompt
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                prompt = f.read()
                # Substitute variables
                prompt = prompt.replace("{company_name}", company_config.get("company_name", "Your Company"))
                prompt = prompt.replace("{assistant_name}", company_config.get("assistant_name", "Nora"))
                return prompt
        
        return "You are a helpful AI assistant."
    
    async def generate(self, text: str, context: Optional[List[dict]] = None) -> str:
        """Generate a response. Override in subclasses."""
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama AI provider (local, free)."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get("ai_model", "llama2")
        logger.info(f"Initialized Ollama provider with model: {self.model}")
    
    async def generate(self, text: str, context: Optional[List[dict]] = None) -> str:
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": text})
            
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=messages
            )
            
            return response["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise


class GeminiProvider(AIProvider):
    """Google Gemini AI provider (requires API key)."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        api_key = config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        
        self.model_name = config.get("gemini_model", "gemini-pro")
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini provider with model: {self.model_name}")
    
    async def generate(self, text: str, context: Optional[List[dict]] = None) -> str:
        try:
            # Build conversation history for Gemini
            history = []
            
            if context:
                for msg in context:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append({"role": role, "parts": [msg["content"]]})
            
            # Start chat with history
            chat = self.model.start_chat(history=history)
            
            # Add system prompt to the user message
            full_prompt = f"{self.system_prompt}\n\nUser: {text}"
            
            # Generate response
            response = await asyncio.to_thread(
                chat.send_message,
                full_prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise


def get_ai_provider(config: dict) -> AIProvider:
    """
    Get the appropriate AI provider based on configuration.
    
    Priority:
    1. If GEMINI_API_KEY is set, use Gemini
    2. Otherwise, use Ollama (default)
    """
    provider_name = config.get("ai_provider", "auto")
    
    if provider_name == "gemini" or (provider_name == "auto" and os.getenv("GEMINI_API_KEY")):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        return GeminiProvider(config)
    
    if not OLLAMA_AVAILABLE:
        raise ImportError("ollama package not installed")
    
    return OllamaProvider(config)
