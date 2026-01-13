# Audio Transcription & Chat Export

Complete guide for audio transcription and chat export features in Nora AI.

---

## 📖 Table of Contents

- [User Guide](#-user-guide)
- [Implementation Details](#-implementation-details)
- [Configuration & Installation](#-configuration--installation)
- [Troubleshooting](#-troubleshooting)

---

## 👤 User Guide

### 🎵 Audio Transcription

Upload audio files and automatically transcribe them to text.

#### Supported Formats:
- `.wav` - WAV Audio
- `.mp3` - MPEG Audio
- `.m4a` - MPEG-4 Audio
- `.ogg` - Ogg Vorbis
- `.flac` - Free Lossless Audio

#### How to Use:
1. Go to the **Files** tab
2. Look for **Audio Transcription** section
3. Drag & drop an audio file or click to browse
4. Wait for transcription to complete
5. Review the transcription result
6. Click **"Insert to Chat"** to add it to your message

#### Features:
- Automatic speech-to-text conversion
- Real-time transcription status
- Option to insert transcription directly into chat
- Works in both English and Norwegian (if audio is in those languages)

### 💾 Chat Export to Files

Save your conversations as text files for future reference.

#### Supported Export Formats:
- `.txt` - Plain text format
- `.md` - Markdown format (better formatting)

#### How to Use:
1. While in chat, click the **"💾 Save"** button in chat header
2. Your chat will be saved to browser history
3. A dialog will ask if you want to export as .txt file
4. Click **"Yes"** to download the conversation
5. The file will be saved with timestamp: `chat_export_YYYYMMDD_HHMMSS.txt`

#### File Contents:
- Timestamp of export
- All messages in conversation
- Formatted with clear USER/ASSISTANT separation
- Markdown format includes nice formatting

### 📁 Document Upload

Continue uploading documents as before - they work with the existing document features.

### Best Practices

#### Audio Transcription
- **Clear speech:** Speak clearly and avoid background noise
- **File quality:** Use good quality audio files
- **Duration:** Keep files under 5 minutes for best results
- **Language:** Audio should match your language setting

#### Chat Export
- **Organize:** Export important conversations regularly
- **Backup:** Keep exported files as backups
- **Share:** Share exported txt files with colleagues
- **Archive:** Use markdown format for better formatting

---

## 🔧 Implementation Details

### What's Been Implemented

#### 1. Audio File Upload & Transcription
- **Upload Support:** .wav, .mp3, .m4a, .ogg, .flac files
- **Location:** Files tab → Audio Transcription section
- **Process:** Drag & drop → Auto-transcribe → Review → Insert to chat
- **No external API keys required** (uses free Google Speech Recognition)

#### 2. Chat Export to File
- **Format Support:** .txt (plain text) and .md (markdown)
- **How:** Click "Save" button → Confirm export → Auto-download
- **Storage:** Files saved in `uploads/exports/` directory
- **Naming:** Auto-timestamped `chat_export_YYYYMMDD_HHMMSS.txt`

#### 3. File Management
- **Uploads directory:** `uploads/` - stores uploaded files
- **Exports directory:** `uploads/exports/` - stores exported chats
- **Temp directory:** `uploads/temp/` - temporary audio processing

### Files Modified

#### Backend (Python)
1. **config.py**
   - Added audio extensions to ALLOWED_EXTENSIONS
   - `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`

2. **documents.py**
   - Added `transcribe_audio(filepath)` function
   - Added `save_chat_to_file(chat_history, format)` function
   - Graceful fallback if SpeechRecognition not installed

3. **server.py**
   - Added `POST /files/transcribe` endpoint
   - Added `POST /chat/save` endpoint
   - Full error handling and validation

#### Frontend (JavaScript/HTML/CSS)
1. **index.html**
   - Added Audio Transcription section in Files tab
   - Drag & drop zone for audio files
   - Transcription result display box
   - "Insert to Chat" button

2. **app.js**
   - `handleAudioFiles()` - Process uploaded audio files
   - `insertTranscriptionToChat()` - Add transcription to chat input
   - `exportChatToFile(format)` - Export conversation to file
   - Updated `setupEventListeners()` for audio drag & drop
   - Modified `saveCurrentChat()` to offer export option

3. **styles.css**
   - `.file-section` - Container for file sections
   - `.transcription-box` - Styled transcription result display
   - Responsive styling for audio upload zone

### Technical Details

#### Audio Transcription
- **Library:** `speech_recognition` (optional, graceful fallback)
- **API:** Google Speech Recognition (free)
- **Max file size:** Browser upload limits (~100MB)
- **Processing:** Async, non-blocking
- **Languages:** Any language supported by browser

#### Chat Export
- **Formats:**
  - **TXT:** Plain text with clear separations
  - **MD:** Markdown with formatting
- **Content:** All messages in order
- **Timestamp:** File creation date included
- **Storage:** Local server storage (can be purged)

### API Endpoints

#### Transcribe Audio File
```
POST /files/transcribe
```
- **Input:** Audio file (.wav, .mp3, .m4a, .ogg, .flac)
- **Output:** Transcribed text
- **Authentication:** Required
- **Processing:** Uses Google Speech Recognition API (free, no key required)

**Example:**
```bash
curl -X POST http://localhost:8000/files/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@recording.wav"
```

#### Export Chat
```
POST /chat/save
```
- **Input:** Chat messages array and format
- **Output:** Downloadable text file
- **Authentication:** Required
- **Storage:** Files saved in `uploads/exports/`

**Example:**
```bash
curl -X POST http://localhost:8000/chat/save \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [...], "format": "txt"}'
```

### Features Comparison

| Feature | Input | Output | Storage |
|---------|-------|--------|---------|
| Audio Transcription | .wav/.mp3/etc | Plain text | Temp (auto-delete) |
| Chat Export | Messages + format | .txt/.md file | uploads/exports/ |
| File Upload | Any allowed type | Organized storage | uploads/ |
| Voice Input | Microphone | Text + Audio | Browser (local) |
| Voice Output | Text | Audio playback | Browser (local) |

---

## ⚙️ Configuration & Installation

### Installation Requirements

#### For Audio Transcription
The system works without additional installation, but for full transcription support, install:

```bash
pip install SpeechRecognition pydub
```

Without these libraries:
- Audio files can still be uploaded
- A placeholder message will appear suggesting installation
- Users can continue using the browser's voice input feature instead

#### Optional: pydub Dependencies
```bash
# For advanced audio processing
pip install pydub

# Also need ffmpeg installed:
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

### Storage Locations

#### Uploaded Audio Files:
- Temporary storage: `uploads/temp/` (auto-cleaned)
- Not permanently stored

#### Exported Chat Files:
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

### Storage Structure

```
local_ai/
├── uploads/
│   ├── temp/              # Temporary audio processing
│   ├── exports/           # Exported chat files
│   │   └── chat_export_*.txt
│   └── [uploaded docs]
├── company_info/          # Company documents
└── gateway/              # Application code
```

### Configuration Options

#### Enable/Disable Features
Modify in `app.js`:
```javascript
// To disable auto-export prompt:
// Comment out the confirm() in saveCurrentChat()

// To disable auto-speak:
// Comment out the speakText() call in addMessage()
```

#### Change Storage Locations
Modify in `config.py`:
```python
UPLOADS_DIR = Path('./uploads')
COMPANY_INFO_DIR = Path('./company_info')
```

#### Add More Audio Formats
Add to `ALLOWED_EXTENSIONS` in `config.py`:
```python
ALLOWED_EXTENSIONS = {
    '.wav', '.mp3', '.m4a', '.ogg', '.flac',
    '.aac',  # Add AAC
    '.wma',  # Add WMA
    # etc.
}
```

---

## 🛠️ Troubleshooting

### Audio Transcription Issues

#### "Transcription unavailable"
- Check internet connection (Google API requires network)
- Try a shorter audio file
- Ensure clear speech in audio
- Try different audio format

**Solution:**
1. Verify internet connection
2. Test with a simple, clear audio file
3. Check audio file is not corrupted
4. Ensure SpeechRecognition library is installed

#### "No microphone found"
- This message is for file upload, not microphone recording
- Check file is valid audio format
- Ensure file has .wav, .mp3, .m4a, .ogg, or .flac extension

#### "File too large"
- Audio files over 100MB may fail to upload
- Compress audio file or reduce quality
- Split long recordings into shorter segments

#### Poor transcription quality
- Ensure clear speech with minimal background noise
- Use higher quality audio files
- Verify audio language matches your language setting
- Try re-recording with better microphone

### Chat Export Issues

#### "No conversation to export"
- Start a chat and send at least one message
- Then try saving again
- Ensure you're in the chat tab (not files or settings)

#### File won't download
- Check browser download settings
- Allow downloads for this site
- Try different export format (txt vs md)
- Check browser's download folder
- Clear browser cache and try again

#### Export is incomplete
- Very long chats may be truncated for performance
- Export still contains full chat history
- Check the downloaded file contents
- Try exporting in smaller sections

#### Permission errors
- Ensure `uploads/exports/` directory exists
- Check write permissions on uploads directory
- Verify you're logged in with valid authentication

### Privacy & Storage

- **Transcription:** Audio files are temporarily stored, then deleted
- **Chat Export:** Files are stored on server in `uploads/exports/` directory
- **Cleanup:** Consider clearing exports directory periodically
- **User Data:** All operations require authentication

### Security Considerations

- **Authentication:** All endpoints require valid token
- **File Validation:** Extensions checked before upload
- **Temp Cleanup:** Temporary files auto-deleted after processing
- **Access Control:** Users can only access their own chats

---

## 📞 Additional Resources

- [Features Guide](../FEATURES.md) - Complete feature documentation
- [Voice Features](VOICE.md) - Voice input and output
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md) - General troubleshooting
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Server setup

### External Documentation
- [SpeechRecognition Library](https://pypi.org/project/SpeechRecognition/)
- [pydub Documentation](https://github.com/jiaaro/pydub)
- [FFmpeg](https://ffmpeg.org/)

---

**Enjoy enhanced communication with audio and export features!** 🚀
