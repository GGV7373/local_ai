import whisper

class WhisperSTTEngine:
    def __init__(self, model_name="base"):
        self.model_name = model_name
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_path):
        print(f"Transcribing audio: {audio_path}")
        result = self.model.transcribe(audio_path)
        return result["text"]

if __name__ == "__main__":
    stt_engine = WhisperSTTEngine(model_name="base")
    audio_file = "sample_audio.wav"  # Replace with your audio file path
    transcription = stt_engine.transcribe(audio_file)
    print("Transcription:", transcription)