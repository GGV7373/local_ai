# Voice Features Guide

Complete guide for voice input and output features in Nora AI, supporting both **English** and **Norwegian**.

---

## 📖 Table of Contents

- [User Guide](#-user-guide)
- [Configuration](#-configuration)
- [Implementation Details](#-implementation-details)
- [Troubleshooting](#-troubleshooting)

---

## 👤 User Guide

### 🎤 Voice Input (Speech Recognition)

#### How to Speak to the AI:

1. **Select Your Language**: Choose your preferred language from the language dropdown:
   - 🇬🇧 English
   - 🇳🇴 Norsk (Norwegian)

2. **Click the Microphone Button**: Click the 🎤 button next to your text input

3. **Start Speaking**: 
   - The button will turn red and show "🎙️ Listening..."
   - Speak clearly and naturally
   - The system will convert your speech to text automatically

4. **Send Your Message**: 
   - The recognized text will appear in the input field
   - Click the send button or press Enter to submit

#### Requirements:
- **Modern Web Browser**: Chrome, Edge, Safari, or Firefox
- **Microphone Access**: Grant microphone permission when prompted
- **Internet Connection**: Speech recognition requires network access

### 🔊 Voice Output (Text-to-Speech)

The AI automatically reads its responses aloud in your selected language:

- **English**: Uses English voice
- **Norwegian**: Uses Norwegian (Bokmål) voice
- **Auto-Disabled**: Long responses (300+ characters) are shortened for natural speech

#### Features:
- Responses are spoken automatically when received
- Click anywhere in the chat to stop the current speech
- You can continue typing while listening to the response

### 🌍 Language Settings

Switch between languages anytime:
- Language selection is **saved** in your browser
- Works across all chat sessions
- Speech recognition and text-to-speech both follow your language choice

### 💡 Tips

- **Speak naturally**: The AI understands conversational speech
- **Pause between sentences**: This helps the system recognize sentence boundaries
- **Spell out complex words**: For technical terms, spell them if they're misrecognized
- **Use context**: Refer back to previous messages for better understanding
- **Adjust volume**: Make sure your speakers are at a comfortable volume

### Keyboard Shortcuts

- **Enter** - Send message
- **Esc** - Stop listening (if recording)

---

## ⚙️ Configuration

### Customizing Voice Behavior

You can customize the voice interaction feature by editing `gateway/static/app.js`.

### 1. Adjust Speech Recognition Settings

In the **Speech Recognition State** section (lines ~16-23):

```javascript
// Change continuous listening
speechRecognition.continuous = true;  // Keep listening for multiple sentences

// Change interim results display
speechRecognition.interimResults = false;  // Don't show live transcription
```

### 2. Change Text-to-Speech Voice Speed and Pitch

In the **`speakText()` function** (around line 186):

```javascript
utterance.rate = 0.95;    // 0.1 (slow) to 1.0 (normal) to 2.0 (fast)
utterance.pitch = 1.0;    // 0.5 (low) to 2.0 (high)
utterance.volume = 1.0;   // 0.0 to 1.0
```

### 3. Adjust Character Limit for Speech

In the **`addMessage()` function** (around line 401):

```javascript
textToSpeak = textToSpeak.substring(0, 300);  // Change 300 to desired length
```

### 4. Add More Languages

In the **`getLanguageCode()` function** (around line 90):

```javascript
const languageMap = {
    'en': 'en-US',
    'no': 'nb-NO',
    'sv': 'sv-SE',     // Swedish
    'da': 'da-DK',     // Danish
    'de': 'de-DE',     // German
    'fr': 'fr-FR',     // French
    'es': 'es-ES',     // Spanish
    'it': 'it-IT',     // Italian
    'pt': 'pt-BR',     // Portuguese (Brazil)
    'ja': 'ja-JP',     // Japanese
    'zh': 'zh-CN',     // Chinese (Simplified)
    'ko': 'ko-KR',     // Korean
};
```

Then update the HTML language dropdown in `gateway/static/index.html`:

```html
<select id="languageSelect" onchange="onLanguageChange()" title="Response Language">
    <option value="en">🇬🇧 English</option>
    <option value="no">🇳🇴 Norsk</option>
    <option value="sv">🇸🇪 Svenska</option>
    <option value="de">🇩🇪 Deutsch</option>
    <option value="fr">🇫🇷 Français</option>
    <!-- Add more as desired -->
</select>
```

### 5. Enable/Disable Auto-Speak Feature

To prevent the AI from automatically speaking responses, find the `addMessage()` function and comment out:

```javascript
// Comment this out to disable auto-speak
// if (type === 'assistant') {
//     ...
// }
```

### 6. Adjust Speech Recognition Timeout

Add this in the `toggleVoiceInput()` function to auto-stop listening after 10 seconds:

```javascript
// Auto-stop after 10 seconds
setTimeout(() => {
    if (isListening) {
        speechRecognition.abort();
        isListening = false;
        stopVoiceInput();
    }
}, 10000);
```

### 7. Customize Error Messages

In the **`speechRecognition.onerror` handler** (around line 156):

```javascript
speechRecognition.onerror = (event) => {
    const errorMessage = {
        'no-speech': 'Your custom message here...',
        'audio-capture': '...',
        'network': '...',
    }[event.error] || `Error: ${event.error}`;
    
    showToast(errorMessage, 'error');
    stopVoiceInput();
};
```

### 8. Style Customization (CSS)

In `gateway/static/styles.css`, modify these sections:

```css
/* Microphone button styling */
.voice-btn {
    width: 50px;
    height: 50px;
    background: var(--bg-tertiary);
    color: var(--accent);
    /* Customize as needed */
}

/* Active listening state */
.voice-btn.active {
    background: rgba(255, 71, 87, 0.2);
    /* Customize color while listening */
}

/* Status indicator */
.voice-status {
    background: rgba(46, 213, 115, 0.1);
    /* Customize status bar appearance */
}
```

### 9. Testing Configurations

After making changes:

1. **Clear Browser Cache**: Press `Ctrl+Shift+Delete`
2. **Hard Refresh**: Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
3. **Test Voice**: Click the microphone button and speak

### Performance Tips

- **Reduce character limit** for faster speech
- **Disable auto-speak** for silent operation
- **Use continuous mode** for longer inputs
- **Adjust speech rate** for comfortable listening

---

## 🔧 Implementation Details

### What's Been Implemented

Nora AI now supports voice input and output in both **English** and **Norwegian**!

### 📁 Files Modified:

1. **`gateway/static/index.html`**
   - Added voice input button (🎤) next to the send button
   - Added voice status indicator showing "🎙️ Listening..."

2. **`gateway/static/app.js`**
   - Added Web Speech API integration for speech recognition
   - Language detection (English: en-US, Norwegian: nb-NO)
   - Text-to-speech function to read AI responses aloud
   - Voice input toggle function with error handling
   - Auto-speaking AI responses with markdown cleanup

3. **`gateway/static/styles.css`**
   - `.voice-btn` - Styled microphone button
   - `.voice-btn.active` - Red pulsing state while listening
   - `.voice-status` - Green status indicator
   - Animations for visual feedback

### 🎯 Key Features:

1. **Voice Input**
   - Click 🎤 button to start listening
   - Automatically transcribes speech to text
   - Respects language selection (English/Norwegian)
   - Shows real-time feedback while listening

2. **Voice Output**
   - AI responses are automatically read aloud
   - Follows your language preference
   - Limits to 300 characters for natural speech
   - Can be stopped by clicking elsewhere

3. **Language Support**
   - English (en-US)
   - Norwegian Bokmål (nb-NO)
   - Language preference is saved in browser storage
   - Both input and output adapt to selected language

### 🔧 Browser Compatibility:

Works in:
- ✅ Chrome/Chromium
- ✅ Edge
- ✅ Safari
- ✅ Firefox

Requires:
- Modern browser with Web Speech API support
- Microphone access granted by user
- Internet connection for speech recognition

### ⚡ Technical Details:

- Uses `window.SpeechRecognition` (or `webkitSpeechRecognition` for Chrome)
- Uses `window.speechSynthesis` for text-to-speech
- Language codes automatically mapped based on user selection
- Speech recognition runs on device and in browser
- No external APIs required for basic speech functionality

---

## 🛠️ Troubleshooting

### 🔴 Common Issues

#### "No speech detected"
- Check that your microphone is working
- Speak clearly and loud enough
- Make sure you're in a quiet environment
- Try again - sometimes it needs a moment to listen

#### "Permission denied"
- Allow microphone access when the browser asks
- Check your browser settings
- Some firewalls may block microphone access

**How to fix permissions:**
- Chrome/Edge: Click lock icon in address bar → allow microphone
- Firefox: Settings → Privacy → Permissions → Microphone
- Safari: System Preferences → Security & Privacy → Microphone

#### Speech recognition not available
- Use a modern browser (Chrome, Edge, Safari, Firefox)
- Older browsers don't support Web Speech API
- Try a different browser if one doesn't work

#### Speech sounds robotic or unclear
- This depends on your browser's built-in voice
- Different browsers have different voice quality
- Try adjusting your browser's voice settings

### 🌐 Network Error

If you see: **"Network error. Check your connection."**

This means the Web Speech API cannot connect to Google's speech recognition servers.

#### Quick Fixes (Try These First)

**1. Check Your Internet Connection**
- Open a new tab and visit: `https://google.com`
- If it loads, your internet is fine
- If not, fix your network connection and try again

**2. Hard Refresh Your Browser**
- Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- This clears browser cache and reloads everything
- Then try the voice feature again

**3. Close Other Tabs Using Microphone**
- Other apps/tabs using microphone can interfere
- Close video calls, recording apps, etc.
- Try voice feature again

**4. Try a Different Browser**
- Chrome ✅ (best support)
- Edge ✅ (best support)
- Firefox ✅ (works well)
- Safari ✅ (works well)

### 🔧 Advanced Troubleshooting

#### Check Browser Console for More Details
1. Press `F12` to open Developer Tools
2. Click **"Console"** tab
3. Try the voice feature again
4. Look for error messages in red
5. Share these messages for better help

#### Browser-Specific Issues

**Chrome/Edge:**
- Go to `chrome://settings/privacy`
- Search for "Microphone"
- Make sure localhost:8000 is not blocked
- Check if site is allowed to use microphone

**Firefox:**
- Go to `about:preferences#privacy`
- Find "Microphone"
- Check permissions for your localhost URL
- Allow if blocked

**Safari:**
- System Preferences → Security & Privacy → Microphone
- Make sure Safari is listed and allowed
- Restart Safari

#### Network/Firewall Issues

If you're behind a corporate firewall:
- The system uses Google's speech recognition servers
- Firewalls may block this communication
- Ask IT to whitelist: `https://www.google.com/speech-api/`
- Or use the browser's built-in speech recognition (may have limitations)

### 📋 Step-by-Step Diagnostic

#### Step 1: Test Internet Connection
```javascript
// In browser console:
fetch('https://www.google.com')
  .then(r => console.log('Connected:', r.status))
  .catch(e => console.log('Network error:', e))
```

If shows 200 or 0 → Internet works  
If shows error → Network problem

#### Step 2: Test Microphone Access
```javascript
// In browser console:
navigator.mediaDevices.enumerateDevices()
  .then(devices => {
    const audioInput = devices.filter(d => d.kind === 'audioinput');
    console.log('Microphones found:', audioInput.length);
    audioInput.forEach(d => console.log(d.label));
  })
```

Should show your microphone(s)  
If empty → Microphone not detected

#### Step 3: Test Speech Recognition API
```javascript
// In browser console:
if (window.SpeechRecognition || window.webkitSpeechRecognition) {
  console.log('Speech Recognition: SUPPORTED');
} else {
  console.log('Speech Recognition: NOT SUPPORTED');
}
```

Should show "SUPPORTED"  
If not → Browser doesn't support it

#### Step 4: Test Speech Recognition Service
```javascript
// In browser console:
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.onerror = (e) => console.log('Error:', e.error);
recognition.onstart = () => console.log('Started listening...');
recognition.lang = 'en-US';
recognition.start();
// Then speak something
```

Should show "Started listening..."  
Then show recognized text or error  
Network error → Service not reachable

### 🌐 Firewall/Proxy Solutions

If your network blocks speech recognition:

#### Option 1: Use Text Input
The application works perfectly with text input when voice is unavailable.

#### Option 2: Contact IT Department
Ask them to whitelist the speech recognition service endpoint.

#### Option 3: Use Different Network
Try from a personal device on a different network to verify the issue.

### 🔄 Workarounds

While troubleshooting:
1. Use text input instead of voice
2. Try from a different network
3. Use a different browser
4. Check for browser updates

### 🆘 Diagnostic Tool

For comprehensive testing, visit:
```
https://YOUR_SERVER_IP/static/voice-diagnostic.html
```

This tool tests:
- Browser support for Speech Recognition
- Microphone access
- Internet connection
- Speech recognition service availability

---

## 📞 Additional Resources

- [Features Guide](../FEATURES.md) - Complete feature documentation
- [Deployment Guide](../deployment/DEPLOYMENT.md) - HTTPS setup for voice features
- [Troubleshooting](../troubleshooting/TROUBLESHOOTING.md) - General troubleshooting

### External Documentation
- [Web Speech API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [SpeechRecognition API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [SpeechSynthesis API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)

---

**Enjoy talking to your AI assistant!** 🚀
