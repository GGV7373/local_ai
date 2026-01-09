from vosk import Model, KaldiRecognizer
import pyaudio
import json
import os

class VoskWakeWordEngine:
    def __init__(self, model_path, wake_word="hey nora"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"VOSK model not found at {model_path}. Please download a model from https://alphacephei.com/vosk/models")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.wake_word = wake_word.lower()
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192
        )
        self.stream.start_stream()
        self.running = False

    def start(self, callback):
        """Start listening for wake word and call callback when detected."""
        print(f"Listening for wake word: '{self.wake_word}'...")
        self.running = True
        while self.running:
            try:
                data = self.stream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    if text:
                        print(f"Heard: {text}")
                    if self.wake_word in text:
                        print("Wake word detected!")
                        callback()
            except Exception as e:
                print(f"Error in wake word detection: {e}")
                break

    def listen_for_wake_word(self):
        """Listen for wake word (blocking, returns when detected)."""
        print(f"Listening for wake word: '{self.wake_word}'...")
        while True:
            data = self.stream.read(4096, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    print(f"Heard: {text}")
                if self.wake_word in text:
                    print("Wake word detected!")
                    return True

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

if __name__ == "__main__":
    model_path = "vosk_model"  # Path to your VOSK model directory
    wake_word_engine = VoskWakeWordEngine(model_path, wake_word="hey nora")

    try:
        wake_word_engine.listen_for_wake_word()
    except KeyboardInterrupt:
        print("Stopping wake-word engine...")
        wake_word_engine.stop()