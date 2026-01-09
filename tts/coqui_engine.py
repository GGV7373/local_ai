import pyttsx3
import os

class CoquiTTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)

    def synthesize(self, text):
        print("Synthesizing text to speech:", text)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error synthesizing speech: {e}")

if __name__ == "__main__":
    tts_engine = CoquiTTSEngine()
    sample_text = "Hello, I am your local AI assistant."
    tts_engine.synthesize(sample_text)