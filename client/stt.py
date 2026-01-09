"""
Speech-to-Text Engine for Desktop Client

Uses OpenAI Whisper for offline speech transcription.
All processing is done locally - no cloud APIs.
"""

import logging
import os
import tempfile
import wave
from typing import Optional

import pyaudio
import whisper

logger = logging.getLogger("client.stt")


class STTEngine:
    """
    Offline speech-to-text using OpenAI Whisper.
    
    Transcribes audio locally without any cloud API calls.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the STT engine.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logger.info("Whisper model loaded successfully")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path: Path to the audio file (WAV format)
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return ""
        
        logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            result = self.model.transcribe(audio_path)
            text = result["text"].strip()
            logger.info(f"Transcription complete: {text[:100]}...")
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def transcribe_from_bytes(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio from bytes.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Sample rate of the audio
            
        Returns:
            Transcribed text
        """
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            
            # Create WAV file
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
            wf.close()
        
        try:
            return self.transcribe(temp_path)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)


class AudioRecorder:
    """
    Records audio from the microphone.
    """
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Sample rate for recording
        """
        self.sample_rate = sample_rate
        self.audio: Optional[pyaudio.PyAudio] = None
    
    def record(self, duration: float, output_path: Optional[str] = None) -> str:
        """
        Record audio from the microphone.
        
        Args:
            duration: Recording duration in seconds
            output_path: Path to save the recording (optional)
            
        Returns:
            Path to the recorded audio file
        """
        logger.info(f"Recording for {duration} seconds...")
        
        self.audio = pyaudio.PyAudio()
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        num_chunks = int(self.sample_rate / 1024 * duration)
        
        for _ in range(num_chunks):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        self.audio.terminate()
        
        # Save to file
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), "command.wav")
        
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        logger.info(f"Recording saved: {output_path}")
        return output_path
    
    def record_bytes(self, duration: float) -> bytes:
        """
        Record audio and return as bytes.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Raw audio bytes
        """
        logger.info(f"Recording for {duration} seconds...")
        
        self.audio = pyaudio.PyAudio()
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        num_chunks = int(self.sample_rate / 1024 * duration)
        
        for _ in range(num_chunks):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        self.audio.terminate()
        
        logger.info("Recording complete")
        return b''.join(frames)


if __name__ == "__main__":
    # Test the STT engine
    logging.basicConfig(level=logging.INFO)
    
    stt = STTEngine(model_name="base")
    recorder = AudioRecorder()
    
    print("Recording in 3 seconds...")
    import time
    time.sleep(3)
    
    audio_path = recorder.record(5)
    text = stt.transcribe(audio_path)
    print(f"Transcription: {text}")
