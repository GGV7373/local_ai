import json
import os
import wave
import pyaudio
from wake_word.vosk_engine import VoskWakeWordEngine
from stt.whisper_engine import WhisperSTTEngine
from llm.llama_backend import LlamaBackend
from tts.coqui_engine import CoquiTTSEngine

def load_config(config_path):
    with open(config_path, "r") as file:
        return json.load(file)

def record_audio(filename, duration=5, sample_rate=16000):
    """Record audio from microphone (Windows compatible)."""
    print(f"Recording for {duration} seconds...")
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=1024
    )
    
    frames = []
    for _ in range(0, int(sample_rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save to WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Recording saved to {filename}")

def main():
    # Load configuration
    config_path = "config.json"
    config = load_config(config_path)

    print("Initializing Local AI Assistant...")
    print(f"Wake word engine: {config.get('wake_word_engine', 'vosk')}")
    print(f"STT engine: {config.get('stt_engine', 'whisper')}")
    print(f"LLM backend: {config.get('llm_backend', 'llama2')}")
    print(f"TTS engine: {config.get('tts_engine', 'pyttsx3')}")
    print()

    # Initialize components
    wake_word_engine = VoskWakeWordEngine("vosk_model", wake_word="hey nora")
    stt_engine = WhisperSTTEngine()
    llm_backend = LlamaBackend(model_name="llama2")
    tts_engine = CoquiTTSEngine()

    def on_wake_word_detected():
        print("\n" + "="*50)
        print("Wake word detected! Listening for command...")
        print("="*50)
        
        # Record audio (Windows compatible)
        record_audio("command.wav", duration=5)
        
        # Transcribe audio to text
        command = stt_engine.transcribe("command.wav")
        print(f"You said: {command}")

        # Generate response from LLM
        response = llm_backend.generate_response(command)
        print(f"Assistant: {response}")

        # Speak the response
        tts_engine.synthesize(response)
        print("\nReady for next command...\n")

    print("Local AI Assistant is ready!")
    print("Say 'hey nora' to activate.")
    print("Press Ctrl+C to stop.\n")

    try:
        # Start wake-word detection
        wake_word_engine.start(on_wake_word_detected)
    except KeyboardInterrupt:
        print("\nShutting down...")
        wake_word_engine.stop()

if __name__ == "__main__":
    main()