"""
Desktop Client Main Application

A local audio client that:
1. Listens for wake word (offline, using VOSK)
2. Records spoken command (local microphone)
3. Transcribes speech to text (offline, using Whisper)
4. Sends ONLY TEXT to the gateway server
5. Receives AI response and speaks it back (offline, using pyttsx3)

This client does NOT:
- Contain any LLM logic
- Call cloud APIs
- Send audio to the server
- Store any secrets
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import threading
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.wake_word import WakeWordEngine
from client.stt import STTEngine, AudioRecorder
from client.tts import TTSEngine
from client.gateway_client import GatewayClient, SyncGatewayClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("client")

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    """Load client configuration from config.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    
    # Default configuration
    return {
        "gateway_url": "ws://localhost:8765/ws",
        "gateway_rest_url": "http://localhost:8765/api/command",
        "use_websocket": True,
        "wake_word": "hey nora",
        "vosk_model_path": "../vosk_model",
        "whisper_model": "base",
        "command_duration": 5,
        "sample_rate": 16000,
        "greeting_message": "Hello boss, how can I help?",
        "tts_rate": 150,
        "tts_volume": 1.0,
        "auto_reconnect": True,
        "reconnect_delay": 5,
        "client_id": None,
        "log_level": "INFO"
    }


class DesktopClient:
    """
    Main desktop client that orchestrates all audio components.
    
    This client runs continuously in the background, listening for the wake word.
    When activated, it records a command, transcribes it locally, sends the TEXT
    to the gateway, and speaks the response.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the desktop client.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or load_config()
        
        # Set log level
        log_level = self.config.get("log_level", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        logger.info("Initializing Desktop Client...")
        
        # Resolve VOSK model path
        vosk_path = self.config.get("vosk_model_path", "../vosk_model")
        if not os.path.isabs(vosk_path):
            vosk_path = os.path.join(os.path.dirname(__file__), vosk_path)
        vosk_path = os.path.abspath(vosk_path)
        
        # Initialize components
        logger.info("Loading wake word engine (VOSK)...")
        self.wake_word_engine = WakeWordEngine(
            model_path=vosk_path,
            wake_word=self.config.get("wake_word", "hey nora"),
            sample_rate=self.config.get("sample_rate", 16000)
        )
        
        logger.info(f"Loading STT engine (Whisper {self.config.get('whisper_model', 'base')})...")
        self.stt_engine = STTEngine(
            model_name=self.config.get("whisper_model", "base")
        )
        
        logger.info("Loading TTS engine (pyttsx3)...")
        self.tts_engine = TTSEngine(
            rate=self.config.get("tts_rate", 150),
            volume=self.config.get("tts_volume", 1.0)
        )
        
        logger.info("Initializing audio recorder...")
        self.recorder = AudioRecorder(
            sample_rate=self.config.get("sample_rate", 16000)
        )
        
        logger.info("Initializing gateway client...")
        self.gateway = SyncGatewayClient(
            rest_url=self.config.get("gateway_rest_url", "http://localhost:8765/api/command"),
            client_id=self.config.get("client_id")
        )
        
        self.running = False
        logger.info("Desktop Client initialized successfully!")
    
    def process_command(self):
        """
        Process a voice command after wake word detection.
        
        1. Speak greeting
        2. Record audio
        3. Transcribe to text (locally)
        4. Send text to gateway
        5. Speak response
        """
        try:
            # Step 1: Speak greeting
            greeting = self.config.get("greeting_message", "Hello boss, how can I help?")
            logger.info(f"Speaking greeting: {greeting}")
            self.tts_engine.speak(greeting)
            
            # Step 2: Record audio
            duration = self.config.get("command_duration", 5)
            logger.info(f"Recording command for {duration} seconds...")
            
            audio_path = os.path.join(tempfile.gettempdir(), "command.wav")
            self.recorder.record(duration, audio_path)
            
            # Step 3: Transcribe to text (LOCAL - no cloud)
            logger.info("Transcribing audio locally...")
            command_text = self.stt_engine.transcribe(audio_path)
            
            if not command_text or not command_text.strip():
                logger.warning("No speech detected")
                self.tts_engine.speak("I didn't catch that. Please try again.")
                return
            
            logger.info(f"You said: {command_text}")
            print(f"\n>>> You: {command_text}")
            
            # Step 4: Send TEXT to gateway (NOT audio!)
            logger.info("Sending text to gateway...")
            response_text = self.gateway.send_command(command_text)
            
            logger.info(f"AI response: {response_text[:100]}...")
            print(f">>> AI: {response_text}\n")
            
            # Step 5: Speak response
            logger.info("Speaking response...")
            self.tts_engine.speak(response_text)
            
            # Clean up temp file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.tts_engine.speak("Sorry, I encountered an error processing your request.")
    
    def run(self):
        """
        Run the desktop client.
        
        Continuously listens for the wake word and processes commands.
        """
        wake_word = self.config.get("wake_word", "hey nora")
        
        print("\n" + "=" * 60)
        print("  LOCAL AI ASSISTANT - DESKTOP CLIENT")
        print("=" * 60)
        print(f"  Wake word: '{wake_word}'")
        print(f"  Gateway: {self.config.get('gateway_rest_url')}")
        print(f"  STT: Whisper ({self.config.get('whisper_model', 'base')})")
        print(f"  TTS: pyttsx3")
        print("=" * 60)
        print(f"\nSay '{wake_word}' to activate.")
        print("Press Ctrl+C to stop.\n")
        
        self.running = True
        
        try:
            # Start wake word detection loop
            self.wake_word_engine.start(self.process_command)
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the desktop client."""
        self.running = False
        self.wake_word_engine.stop()
        logger.info("Desktop Client stopped")


def main():
    """Main entry point."""
    config = load_config()
    client = DesktopClient(config)
    client.run()


if __name__ == "__main__":
    main()
