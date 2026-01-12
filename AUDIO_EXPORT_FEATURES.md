# Audio Transcription & Chat Export Features

## New Capabilities

Your Nora AI application now supports:

### 1. 🎵 Audio Transcription
Upload audio files and automatically transcribe them to text.

**Supported Formats:**
- `.wav` - WAV Audio
- `.mp3` - MPEG Audio
- `.m4a` - MPEG-4 Audio
- `.ogg` - Ogg Vorbis
- `.flac` - Free Lossless Audio

**How to Use:**
1. Go to the **Files** tab
2. Look for **Audio Transcription** section
3. Drag & drop an audio file or click to browse
4. Wait for transcription to complete
5. Review the transcription result
6. Click **"Insert to Chat"** to add it to your message

**Features:**
- Automatic speech-to-text conversion
- Real-time transcription status
- Option to insert transcription directly into chat
- Works in both English and Norwegian (if audio is in those languages)

### 2. 💾 Chat Export to Files
Save your conversations as text files for future reference.

**Supported Export Formats:**
- `.txt` - Plain text format
- `.md` - Markdown format (better formatting)

**How to Use:**
1. While in chat, click the **"💾 Save"** button in chat header
2. Your chat will be saved to browser history
3. A dialog will ask if you want to export as .txt file
4. Click **"Yes"** to download the conversation
5. The file will be saved with timestamp: `chat_export_YYYYMMDD_HHMMSS.txt`

**File Contents:**
- Timestamp of export
- All messages in conversation
- Formatted with clear USER/ASSISTANT separation
- Markdown format includes nice formatting

### 3. 📁 Document Upload
Continue uploading documents as before - they work with the existing document features.

---

## Backend Features

### Audio Transcription Endpoint
```
POST /files/transcribe
```
- **Input:** Audio file (.wav, .mp3, .m4a, .ogg, .flac)
- **Output:** Transcribed text
- **Authentication:** Required
- **Processing:** Uses Google Speech Recognition API (free, no key required)

### Chat Export Endpoint
```
POST /chat/save
```
- **Input:** Chat messages array and format
- **Output:** Downloadable text file
- **Authentication:** Required
- **Storage:** Files saved in `uploads/exports/`

---

## Installation Requirements

### For Audio Transcription
The system works without additional installation, but for full transcription support, install:

```bash
pip install SpeechRecognition pydub
```

Without these libraries:
- Audio files can still be uploaded
- A placeholder message will appear suggesting installation
- Users can continue using the browser's voice input feature instead

### Optional: pydub Dependencies
```bash
# For advanced audio processing
pip install pydub

# Also need ffmpeg installed:
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

---

## Configuration

### Storage Locations

**Uploaded Audio Files:**
- Temporary storage: `uploads/temp/` (auto-cleaned)
- Not permanently stored

**Exported Chat Files:**
- Location: `uploads/exports/`
- Naming: `chat_export_YYYYMMDD_HHMMSS.txt`
- Files stay in storage for download

### Allowed File Extensions

Updated in `config.py`:
```python
ALLOWED_EXTENSIONS = {
    # ... existing extensions ...
    '.wav', '.mp3', '.m4a', '.ogg', '.flac'  # Audio files
}
```

---

## Troubleshooting

### Audio Transcription Issues

**"Transcription unavailable"**
- Check internet connection (Google API requires network)
- Try a shorter audio file
- Ensure clear speech in audio
- Try different audio format

**"No microphone found"**
- This is for file upload, not microphone recording
- Check file is valid audio format

### Chat Export Issues

**"No conversation to export"**
- Start a chat and send at least one message
- Then try saving again

**File won't download**
- Check browser download settings
- Try different export format (txt vs md)
- Check browser's download folder

**Export is incomplete**
- Very long chats may be truncated for performance
- Export still contains full chat history
- Check the downloaded file contents

---

## Best Practices

### Audio Transcription
- **Clear speech:** Speak clearly and avoid background noise
- **File quality:** Use good quality audio files
- **Duration:** Keep files under 5 minutes for best results
- **Language:** Audio should match your language setting

### Chat Export
- **Organize:** Export important conversations regularly
- **Backup:** Keep exported files as backups
- **Share:** Share exported txt files with colleagues
- **Archive:** Use markdown format for better formatting

---

## Privacy & Storage

- **Transcription:** Audio files are temporarily stored, then deleted
- **Chat Export:** Files are stored on server in `uploads/exports/` directory
- **Cleanup:** Consider clearing exports directory periodically
- **User Data:** All operations require authentication

---

## API Examples

### Transcribe Audio File
```bash
curl -X POST http://localhost:8000/files/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@recording.wav"
```

### Export Chat
```bash
curl -X POST http://localhost:8000/chat/save \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [...],
    "format": "txt"
  }'
```

---

## Files Modified

1. **config.py** - Added audio file extensions to ALLOWED_EXTENSIONS
2. **documents.py** - Added `transcribe_audio()` and `save_chat_to_file()` functions
3. **server.py** - Added `/files/transcribe` and `/chat/save` endpoints
4. **index.html** - Added audio upload section and transcription result display
5. **app.js** - Added audio handling and chat export functions
6. **styles.css** - Added styles for transcription box and file sections

---

Enjoy transcribing and exporting your conversations! 🎉
