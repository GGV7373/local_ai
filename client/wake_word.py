"""
Wake Word Engine for Desktop Client

Uses VOSK for offline wake word detection.
Runs continuously in the background, listening for the configured wake word.
"""

import json
import logging
import os
from typing import Callable, Optional

from vosk import Model, KaldiRecognizer
import pyaudio

logger = logging.getLogger("client.wake_word")


class WakeWordEngine:
    """
    Offline wake word detection using VOSK.
    
    Listens to microphone input and triggers callback when wake word is detected.
    """
    
    def __init__(
        self,
        model_path: str,
        wake_word: str = "hey nora",
        sample_rate: int = 16000
    ):
        """
        Initialize the wake word engine.
        
        Args:
            model_path: Path to the VOSK model directory
            wake_word: The phrase to listen for (case insensitive)
            sample_rate: Audio sample rate in Hz
        """
        self.model_path = model_path
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.running = False
        self.stream: Optional[pyaudio.Stream] = None
        self.audio: Optional[pyaudio.PyAudio] = None
        
        # Validate model path
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"VOSK model not found at {model_path}. "
                "Please download a model from https://alphacephei.com/vosk/models"
            )
        
        # Load VOSK model
        logger.info(f"Loading VOSK model from {model_path}")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        
        logger.info(f"Wake word engine initialized. Wake word: '{wake_word}'")
    
    def _init_audio(self):
        """Initialize audio input stream."""
        if self.audio is None:
            self.audio = pyaudio.PyAudio()
        
        if self.stream is None or not self.stream.is_active():
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=8192
            )
            self.stream.start_stream()
    
    def _cleanup_audio(self):
        """Clean up audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def start(self, on_wake_word: Callable[[], None]):
        """
        Start listening for the wake word.
        
        Args:
            on_wake_word: Callback function to call when wake word is detected
        """
        self._init_audio()
        self.running = True
        
        logger.info(f"Listening for wake word: '{self.wake_word}'...")
        
        while self.running:
            try:
                data = self.stream.read(4096, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    if text:
                        logger.debug(f"Heard: {text}")
                    
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        on_wake_word()
                        
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
                if not self.running:
                    break
    
    def listen_once(self) -> bool:
        """
        Listen for the wake word (blocking, returns when detected).
        
        Returns:
            True when wake word is detected
        """
        self._init_audio()
        
        logger.info(f"Listening for wake word: '{self.wake_word}'...")
        
        while True:
            try:
                data = self.stream.read(4096, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    if text:
                        logger.debug(f"Heard: {text}")
                    
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        return True
                        
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
                return False
    
    def stop(self):
        """Stop listening for wake word."""
        self.running = False
        self._cleanup_audio()
        logger.info("Wake word engine stopped")


if __name__ == "__main__":
    # Test the wake word engine
    logging.basicConfig(level=logging.INFO)
    
    engine = WakeWordEngine("../vosk_model", wake_word="hey nora")
    
    try:
        def on_detected():
            print(">>> Wake word detected! <<<")
        
        engine.start(on_detected)
    except KeyboardInterrupt:
        engine.stop()
