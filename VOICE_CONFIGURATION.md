# Voice Feature Configuration Guide

## Customizing Voice Behavior

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
        'no-speech': 'Din egne feilmelding her...',
        'audio-capture': '...',
        'network': '...',
    }[event.error] || `Feil: ${event.error}`;
    
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

### 10. Troubleshooting Custom Changes

If voice stops working after changes:

1. Check browser console for errors (`F12` → Console tab)
2. Verify no syntax errors in JavaScript
3. Ensure language codes are valid (use standard RFC 5646 format)
4. Test in a different browser to isolate issues

## Example: Norwegian-Only Version

If you want ONLY Norwegian:

```javascript
// In getLanguageCode()
function getLanguageCode() {
    return 'nb-NO';  // Always Norwegian
}
```

Remove the English option from the HTML dropdown and remove the language selection feature.

## Performance Tips

- Limit speech recognition continuous mode (drain resources)
- Reduce interim results for faster responsiveness
- Use shorter character limits for auto-speak to avoid long delays
- Test on slower devices and adjust accordingly

Need help? Check [VOICE_GUIDE.md](VOICE_GUIDE.md) for user-facing documentation.
