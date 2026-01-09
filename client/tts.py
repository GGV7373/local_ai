"""
Text-to-Speech Engine for Desktop Client

Uses pyttsx3 for offline speech synthesis.
All processing is done locally - no cloud APIs.
"""

import logging
from typing import Optional

import pyttsx3

logger = logging.getLogger("client.tts")


class TTSEngine:
    """
    Offline text-to-speech using pyttsx3.
    
    Synthesizes speech locally without any cloud API calls.
    """
    
    def __init__(self, rate: int = 150, volume: float = 1.0):
        """
        Initialize the TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        logger.info("Initializing TTS engine")
        
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Get available voices
        voices = self.engine.getProperty('voices')
        if voices:
            logger.info(f"Available voices: {len(voices)}")
            # Use default voice (usually first one)
            self.engine.setProperty('voice', voices[0].id)
        
        logger.info("TTS engine initialized successfully")
    
    def speak(self, text: str):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
        """
        if not text:
            logger.warning("Empty text provided to TTS")
            return
        
        logger.info(f"Speaking: {text[:50]}...")
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    def set_rate(self, rate: int):
        """Set speech rate."""
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.engine.setProperty('volume', min(1.0, max(0.0, volume)))
    
    def set_voice(self, voice_id: str):
        """Set voice by ID."""
        self.engine.setProperty('voice', voice_id)
    
    def get_voices(self) -> list:
        """Get list of available voices."""
        return self.engine.getProperty('voices')


if __name__ == "__main__":
    # Test the TTS engine
    logging.basicConfig(level=logging.INFO)
    
    tts = TTSEngine()
    tts.speak("Hello! I am your local AI assistant. How can I help you today?")
