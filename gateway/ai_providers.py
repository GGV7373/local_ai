"""
Nora AI - AI Provider Module (Ollama & Gemini 2.x)
Linux Private Server Edition with Streaming Support
"""
import os
import logging
import asyncio
import aiohttp
import json
from typing import Tuple, AsyncGenerator, Optional

try:
    from ollama import AsyncClient as OllamaAsyncClient
    from ollama import ResponseError as OllamaResponseError
    OLLAMA_LIB_AVAILABLE = True
except ImportError:
    OLLAMA_LIB_AVAILABLE = False
    OllamaAsyncClient = None
    OllamaResponseError = Exception

from config import AI_SERVER_URL, AI_MODEL, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODELS

logger = logging.getLogger(__name__)


def get_ollama_client():
    """Get an Ollama AsyncClient configured with the correct host."""
    if not OLLAMA_LIB_AVAILABLE:
        return None
    return OllamaAsyncClient(host=AI_SERVER_URL)


# =============================================================================
# Ollama Functions (with Streaming)
# =============================================================================
async def ask_ollama(
    prompt: str, 
    context: str = "", 
    system_prompt: str = "",
    language: str = "en",
    max_retries: int = 3
) -> Tuple[bool, str]:
    """
    Send a question to Ollama using the official library.
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
    
    # Use official ollama library if available
    if OLLAMA_LIB_AVAILABLE:
        for attempt in range(max_retries):
            try:
                client = get_ollama_client()
                response = await client.chat(
                    model=AI_MODEL,
                    messages=messages
                )
                content = response.message.content
                return True, content
                
            except OllamaResponseError as e:
                logger.error(f"Ollama response error: {e}")
                if e.status_code == 404:
                    return False, f"Model '{AI_MODEL}' not found. Run: ollama pull {AI_MODEL}"
                return False, str(e)
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Ollama error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    if "connect" in error_msg.lower() or "connection" in error_msg.lower():
                        return False, (
                            "Failed to connect to Ollama. Please check that:\n"
                            "1. Ollama is installed and running\n"
                            "2. Run 'ollama serve' or 'systemctl start ollama'\n"
                            f"3. Ollama is accessible at: {AI_SERVER_URL}"
                        )
                    return False, error_msg
        
        return False, "Failed to connect to Ollama after multiple attempts"
    
    # Fallback to aiohttp if ollama library not available
    return await _ask_ollama_http(messages, max_retries)


async def stream_ollama(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    model: str = None
) -> AsyncGenerator[str, None]:
    """
    Stream response from Ollama.
    Yields chunks of text as they arrive.
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
    
    use_model = model or AI_MODEL
    
    # Use official ollama library for streaming
    if OLLAMA_LIB_AVAILABLE:
        try:
            client = get_ollama_client()
            async for chunk in await client.chat(
                model=use_model,
                messages=messages,
                stream=True
            ):
                if chunk.message and chunk.message.content:
                    yield chunk.message.content
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"\n\n[Error: {str(e)}]"
            return
    else:
        # Fallback to HTTP streaming
        async for chunk in _stream_ollama_http(messages, use_model):
            yield chunk


async def _stream_ollama_http(messages: list, model: str) -> AsyncGenerator[str, None]:
    """HTTP streaming fallback for Ollama."""
    try:
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{AI_SERVER_URL}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                if response.status != 200:
                    yield f"[Error: HTTP {response.status}]"
                    return
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'message' in data and 'content' in data['message']:
                                yield data['message']['content']
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        logger.error(f"Ollama HTTP streaming error: {e}")
        yield f"\n\n[Error: {str(e)}]"


async def _ask_ollama_http(messages: list, max_retries: int = 3) -> Tuple[bool, str]:
    """Fallback HTTP method if ollama library is not available."""
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
                        logger.error(f"Ollama HTTP error {response.status}: {error_text}")
                        if response.status == 404:
                            return False, f"Model '{AI_MODEL}' not found. Run: ollama pull {AI_MODEL}"
                        
        except asyncio.TimeoutError:
            logger.warning(f"Ollama timeout (attempt {attempt + 1}/{max_retries})")
        except aiohttp.ClientError as e:
            logger.warning(f"Ollama connection error (attempt {attempt + 1}/{max_retries}): {e}")
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}")
            return False, str(e)
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
    
    return False, (
        "Failed to connect to Ollama. Please check that:\n"
        "1. Ollama is installed (https://ollama.com/download)\n"
        "2. Ollama is running (run 'ollama serve' in terminal)\n"
        f"3. Ollama is accessible at: {AI_SERVER_URL}"
    )


async def ask_gemini(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    model: str = None
) -> Tuple[bool, str]:
    """
    Send a question to Google Gemini API (2.x models supported).
    Returns (success, response_or_error).
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        return False, "Gemini API key not configured. Set GEMINI_API_KEY in your .env file."
    
    language_instructions = {
        "no": "Svar alltid på norsk.",
        "en": "Always respond in English."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    
    # Use provided model or default from config
    use_model = model or GEMINI_MODEL or "gemini-2.0-flash"
    
    # Validate model name
    if not use_model.startswith("gemini"):
        use_model = "gemini-2.0-flash"
    
    # Build the request based on model version
    # Gemini 2.x uses system_instruction, 1.x uses inline
    is_2x = "2.0" in use_model or "2.5" in use_model
    
    try:
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            if is_2x:
                # Gemini 2.x API format with system instruction
                request_body = {
                    "system_instruction": {
                        "parts": [{"text": f"{system_prompt}\n\n{lang_instruction}"}]
                    },
                    "contents": [
                        {
                            "parts": [
                                {"text": f"Context:\n{context}\n\nUser: {prompt}" if context else prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.95,
                        "maxOutputTokens": 8192
                    }
                }
            else:
                # Gemini 1.x format (inline system prompt)
                full_prompt = f"{system_prompt}\n\n{lang_instruction}"
                if context:
                    full_prompt += f"\n\nContext:\n{context}"
                full_prompt += f"\n\nUser: {prompt}"
                
                request_body = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
            
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{use_model}:generateContent?key={GEMINI_API_KEY}",
                json=request_body,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return True, text
                    except (KeyError, IndexError):
                        logger.error(f"Invalid Gemini response: {data}")
                        return False, "Invalid response format from Gemini"
                else:
                    error = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error}")
                    
                    if response.status == 400 and "API_KEY" in error:
                        return False, "Invalid Gemini API key. Check your GEMINI_API_KEY."
                    elif response.status == 404:
                        return False, f"Gemini model '{use_model}' not found. Try gemini-2.0-flash."
                    
                    return False, f"Gemini API error: {response.status}"
                    
    except asyncio.TimeoutError:
        return False, "Gemini request timed out"
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return False, str(e)


async def stream_gemini(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    model: str = None
) -> AsyncGenerator[str, None]:
    """
    Stream response from Gemini API.
    Yields chunks of text as they arrive.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        yield "[Error: Gemini API key not configured]"
        return
    
    language_instructions = {
        "no": "Svar alltid på norsk.",
        "en": "Always respond in English."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    use_model = model or GEMINI_MODEL or "gemini-2.0-flash"
    
    if not use_model.startswith("gemini"):
        use_model = "gemini-2.0-flash"
    
    is_2x = "2.0" in use_model or "2.5" in use_model
    
    try:
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            if is_2x:
                request_body = {
                    "system_instruction": {
                        "parts": [{"text": f"{system_prompt}\n\n{lang_instruction}"}]
                    },
                    "contents": [
                        {
                            "parts": [
                                {"text": f"Context:\n{context}\n\nUser: {prompt}" if context else prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.95,
                        "maxOutputTokens": 8192
                    }
                }
            else:
                full_prompt = f"{system_prompt}\n\n{lang_instruction}"
                if context:
                    full_prompt += f"\n\nContext:\n{context}"
                full_prompt += f"\n\nUser: {prompt}"
                request_body = {"contents": [{"parts": [{"text": full_prompt}]}]}
            
            # Use streamGenerateContent endpoint
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{use_model}:streamGenerateContent?key={GEMINI_API_KEY}&alt=sse",
                json=request_body,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    yield f"[Error: {response.status} - {error[:100]}]"
                    return
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if 'candidates' in data:
                                for candidate in data['candidates']:
                                    if 'content' in candidate and 'parts' in candidate['content']:
                                        for part in candidate['content']['parts']:
                                            if 'text' in part:
                                                yield part['text']
                        except json.JSONDecodeError:
                            continue
                            
    except Exception as e:
        logger.error(f"Gemini streaming error: {e}")
        yield f"\n\n[Error: {str(e)}]"


# =============================================================================
# Unified AI Functions
# =============================================================================
async def ask_ai(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    provider: str = "ollama",
    model: str = None,
    fallback: bool = True
) -> Tuple[str, str]:
    """
    Ask AI using specified provider with optional fallback.
    Returns (response, provider_used).
    """
    result = ""
    
    # Try primary provider
    if provider == "gemini":
        success, result = await ask_gemini(prompt, context, system_prompt, language, model)
        if success:
            return result, "gemini"
    else:
        success, result = await ask_ollama(prompt, context, system_prompt, language)
        if success:
            return result, "ollama"
    
    # Try fallback if enabled
    if fallback:
        fallback_provider = "gemini" if provider == "ollama" else "ollama"
        logger.warning(f"{provider} failed, trying fallback: {fallback_provider}")
        
        if fallback_provider == "gemini":
            success, fallback_result = await ask_gemini(prompt, context, system_prompt, language)
        else:
            success, fallback_result = await ask_ollama(prompt, context, system_prompt, language)
        
        if success:
            return fallback_result + f"\n\n*(Using {fallback_provider} as fallback)*", fallback_provider
    
    return f"Error: {result}", provider


async def stream_ai(
    prompt: str,
    context: str = "",
    system_prompt: str = "",
    language: str = "en",
    provider: str = "ollama",
    model: str = None
) -> AsyncGenerator[str, None]:
    """
    Stream AI response using specified provider.
    Yields chunks of text as they arrive.
    """
    if provider == "gemini":
        async for chunk in stream_gemini(prompt, context, system_prompt, language, model):
            yield chunk
    else:
        async for chunk in stream_ollama(prompt, context, system_prompt, language, model):
            yield chunk


async def check_ollama_status() -> dict:
    """Check if Ollama is running and accessible."""
    if OLLAMA_LIB_AVAILABLE:
        try:
            client = get_ollama_client()
            models = await client.list()
            model_names = [m.model for m in models.models] if hasattr(models, 'models') else []
            return {
                "status": "connected",
                "models": model_names,
                "url": AI_SERVER_URL
            }
        except Exception as e:
            return {"status": "disconnected", "message": str(e)}
    
    # Fallback to HTTP check
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
    if OLLAMA_LIB_AVAILABLE:
        try:
            client = get_ollama_client()
            models = await client.list()
            return [{"name": m.model} for m in models.models] if hasattr(models, 'models') else []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    # Fallback to HTTP
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
