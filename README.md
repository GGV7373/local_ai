# Local AI Assistant

A fully offline, privacy-focused AI assistant for small teams. Uses only free and open-source components.

## Features

- **Wake-word detection**: Say "hey nora" to activate
- **Speech-to-text**: Whisper for high-quality transcription (supports English and Norwegian)
- **Language model**: Ollama with LLaMA2 for local AI responses
- **Text-to-speech**: pyttsx3 for voice output

## Requirements

- Python 3.8+
- Windows 10/11
- Microphone
- [Ollama](https://ollama.ai) installed and running

## Installation

1. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Download VOSK model** (for wake-word detection):
   ```powershell
   # Download from https://alphacephei.com/vosk/models
   # Extract to 'vosk_model' folder in project root
   ```

3. **Install and start Ollama**:
   ```powershell
   # Download from https://ollama.com
   # Then run:
   ollama serve
   ollama pull llama2
   ```

## Usage

1. **Start Ollama** (in a separate terminal):
   ```powershell
   ollama serve
   ```

2. **Run the assistant**:
   ```powershell
   python orchestrator.py
   ```

3. **Activate with voice**:
   - Say "hey nora" to wake the assistant
   - Speak your command (5 seconds to record)
   - The assistant will respond via voice

## Configuration

Edit `config.json` to change settings:

```json
{
  "wake_word_engine": "vosk",
  "stt_engine": "whisper",
  "llm_backend": "llama2",
  "tts_engine": "pyttsx3"
}
```

## Project Structure

```
local_ai/
├── wake_word/           # Wake-word detection engines
│   └── vosk_engine.py   # VOSK-based wake-word detector
├── stt/                 # Speech-to-text engines
│   └── whisper_engine.py
├── llm/                 # Language model backends
│   └── llama_backend.py # Ollama integration
├── tts/                 # Text-to-speech engines
│   └── coqui_engine.py  # pyttsx3-based TTS
├── orchestrator.py      # Main application
├── config.json          # Configuration
├── setup.py             # Setup script
└── requirements.txt     # Python dependencies
```

## Troubleshooting

### "No module named 'vosk'"
```powershell
pip install vosk
```

### "VOSK model not found"
Download a model from https://alphacephei.com/vosk/models and extract to `vosk_model/`

### "Could not connect to Ollama"
Make sure Ollama is running:
```powershell
ollama serve
```

### "No LLaMA model found"
Pull a model:
```powershell
ollama pull llama2
```

## License

MIT License - Free for commercial and personal use.
