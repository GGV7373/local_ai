"""
Nora AI - AI Provider Module (Ollama & Gemini)
"""
import os
import logging
import asyncio
import aiohttp
from typing import Optional, Tuple

from config import AI_SERVER_URL, AI_MODEL, GEMINI_API_KEY

logger = logging.getLogger(__name__)


async def ask_ollama(
    prompt: str, 
    context: str = "", 
    system_prompt: str = "",
    language: str = "en",
    max_retries: int = 3
) -> Tuple[bool, str]:
    """
    Send a question to Ollama and get a response.
    Returns (success, response_or_error).
    """
    language_instructions = {
        "no": "Svar alltid på norsk. Du er en hyggelig og profesjonell assistent.",
        "en": "Always respond in English. You are a friendly and professional assistant."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    
    full_system = f"{system_prompt}\n\n{lang_instruction}"
    if context:
        full_system += f"\n\nHere is relevant company context:\n{context}"
    
    messages = [
        {"role": "system", "content": full_system},
        {"role": "user", "content": prompt}
    ]
    
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{AI_SERVER_URL}/api/chat",
                    json={
                        "model": AI_MODEL,
                        "messages": messages,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, data.get("message", {}).get("content", "No response")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"Ollama timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except aiohttp.ClientError as e:
            logger.warning(f"Ollama connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}")
            return False, str(e)
    
    return False, "Failed to connect to Ollama after multiple attempts"


async def ask_gemini(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en"
) -> Tuple[bool, str]:
    """
    Send a question to Google Gemini API.
    Returns (success, response_or_error).
    """
    if not GEMINI_API_KEY:
        return False, "Gemini API key not configured"
    
    language_instructions = {
        "no": "Svar alltid på norsk.",
        "en": "Always respond in English."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    
    full_prompt = f"{system_prompt}\n\n{lang_instruction}"
    if context:
        full_prompt += f"\n\nContext:\n{context}"
    full_prompt += f"\n\nUser: {prompt}"
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                },
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return True, text
                    except (KeyError, IndexError):
                        return False, "Invalid response format from Gemini"
                else:
                    error = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error}")
                    return False, f"Gemini API error: {response.status}"
                    
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return False, str(e)


async def ask_ai(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    provider: str = "ollama",
    fallback: bool = True
) -> Tuple[str, str]:
    """
    Ask AI using specified provider with optional fallback.
    Returns (response, provider_used).
    """
    providers = {
        "ollama": ask_ollama,
        "gemini": ask_gemini
    }
    
    # Try primary provider
    primary_func = providers.get(provider)
    if primary_func:
        if provider == "ollama":
            success, result = await ask_ollama(prompt, context, system_prompt, language)
        else:
            success, result = await ask_gemini(prompt, context, system_prompt, language)
        
        if success:
            return result, provider
    
    # Try fallback if enabled
    if fallback:
        fallback_provider = "gemini" if provider == "ollama" else "ollama"
        fallback_func = providers.get(fallback_provider)
        
        if fallback_func:
            if fallback_provider == "ollama":
                success, result = await ask_ollama(prompt, context, system_prompt, language)
            else:
                success, result = await ask_gemini(prompt, context, system_prompt, language)
            
            if success:
                return result, fallback_provider
    
    return f"Error: {result}", provider


async def check_ollama_status() -> dict:
    """Check if Ollama is running and accessible."""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{AI_SERVER_URL}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m.get("name", "unknown") for m in data.get("models", [])]
                    return {
                        "status": "connected",
                        "models": models,
                        "url": AI_SERVER_URL
                    }
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "disconnected", "message": str(e)}


async def list_ollama_models() -> list:
    """List available models in Ollama."""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{AI_SERVER_URL}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
    except Exception as e:
        logger.error(f"Error listing models: {e}")
    return []
