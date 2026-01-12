# Voice Feature Troubleshooting - Network Error Fix

## 🔴 Network Error While Testing Voice

If you see: **"Network error. Check your connection."**

This means the Web Speech API cannot connect to Google's speech recognition servers.

---

## ✅ Quick Fixes (Try These First)

### 1. **Check Your Internet Connection**
- Open a new tab and visit: `https://google.com`
- If it loads, your internet is fine
- If not, fix your network connection and try again

### 2. **Hard Refresh Your Browser**
- Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- This clears browser cache and reloads everything
- Then try the voice feature again

### 3. **Check Microphone Permissions**
- Browser asks for microphone access the first time
- Make sure you clicked **"Allow"** in the permission popup
- If you clicked "Block":
  - Chrome/Edge: Click lock icon in address bar → allow microphone
  - Firefox: Settings → Privacy → Permissions → Microphone
  - Safari: System Preferences → Security & Privacy → Microphone

### 4. **Close Other Tabs Using Microphone**
- Other apps/tabs using microphone can interfere
- Close video calls, recording apps, etc.
- Try voice feature again

### 5. **Try a Different Browser**
- Chrome ✅ (best support)
- Edge ✅ (best support)
- Firefox ✅ (works well)
- Safari ✅ (works well)
- Internet Explorer ❌ (not supported)

---

## 🔧 Advanced Troubleshooting

### Check Browser Console for More Details
1. Press `F12` to open Developer Tools
2. Click **"Console"** tab
3. Try the voice feature again
4. Look for error messages in red
5. Share these messages for better help

### Browser-Specific Issues

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

### Network/Firewall Issues

If you're behind a corporate firewall:
- The system uses Google's speech recognition servers
- Firewalls may block this communication
- Ask IT to whitelist: `https://www.google.com/speech-api/`
- Or use the browser's built-in speech recognition (may have limitations)

---

## 📋 Step-by-Step Diagnostic

### Step 1: Test Internet Connection
```
In browser console:
> fetch('https://www.google.com')
  .then(r => console.log('Connected:', r.status))
  .catch(e => console.log('Network error:', e))
```

If shows 200 or 0 → Internet works  
If shows error → Network problem

### Step 2: Test Microphone Access
```
In browser console:
> navigator.mediaDevices.enumerateDevices()
  .then(devices => {
    const audioInput = devices.filter(d => d.kind === 'audioinput');
    console.log('Microphones found:', audioInput.length);
    audioInput.forEach(d => console.log(d.label));
  })
```

Should show your microphone(s)  
If empty → Microphone not detected

### Step 3: Test Speech Recognition API
```
In browser console:
> if (window.SpeechRecognition || window.webkitSpeechRecognition) {
    console.log('Speech Recognition: SUPPORTED');
  } else {
    console.log('Speech Recognition: NOT SUPPORTED');
  }
```

Should show "SUPPORTED"  
If not → Browser doesn't support it

### Step 4: Test Speech Recognition Service
```
In browser console:
> const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.onerror = (e) => console.log('Error:', e.error);
recognition.onstart = () => console.log('Started listening...');
recognition.lang = 'en-US';
recognition.start();
// Then speak something
```

Should show "Started listening..."  
Then show recognized text or error  
Network error → Service not reachable

---

## 🌐 Firewall/Proxy Solutions

If your network blocks speech recognition:

### Option 1: Use Local Speech Recognition
Edit `gateway/static/app.js` and add custom error handling (advanced):
```javascript
// Check if network error, offer alternatives
if (event.error === 'network') {
    showToast('Cloud speech recognition unavailable. Use text input instead.', 'warning');
}
```

### Option 2: Install Optional Package for Local Processing
```bash
pip install SpeechRecognition pydub
```

Then modify `documents.py` to use local processing for uploaded audio files.

### Option 3: Use Different Speech Service
Contact support to integrate with alternative services like:
- Azure Speech Services
- AWS Transcribe
- IBM Watson

---

## 🔄 Workarounds While Fixing

### Temporary Workarounds

1. **Text Input** - Continue using keyboard
2. **Audio Upload** - Record audio, upload .wav file
3. **Voice Output** - Still works (AI speaks)
4. **Export Chat** - Save conversations normally

### Disable Voice Feature Temporarily
Edit `gateway/static/index.html`, comment out:
```html
<!-- <button class="voice-btn" id="voiceBtn" ...>🎤</button> -->
```

Then refresh page.

---

## 📞 Reporting the Issue

If the issue persists, check:

1. ✅ Browser: Which one? (Chrome, Firefox, Safari, Edge)
2. ✅ OS: Windows, Mac, Linux?
3. ✅ Internet: Working fine elsewhere?
4. ✅ Microphone: Detected in settings?
5. ✅ Console errors: Any error messages?
6. ✅ VPN/Proxy: Using one?
7. ✅ Firewall: Corporate/restricted network?

Share this info for better support.

---

## 🎯 Most Common Solutions

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| Network error | No internet | Check connection |
| Network error | Firewall blocking | Use VPN or different network |
| Network error | Browser cache | Ctrl+Shift+R |
| No microphone | Permission denied | Allow in browser settings |
| No microphone | Hardware issue | Check system microphone |
| Not working | Browser incompatible | Use Chrome/Edge |
| Not working | Permission never asked | Clear browser data |

---

## ✨ Prevention Tips

### For Best Performance
1. Use a modern browser (Chrome, Edge, Safari, Firefox)
2. Keep browser updated to latest version
3. Use stable internet connection (not mobile hotspot)
4. Quiet environment (less background noise)
5. Speak clearly and at normal volume
6. Microphone close to mouth
7. Check microphone is not muted

### Regular Maintenance
- Clear browser cache monthly: `Ctrl+Shift+Delete`
- Update browser regularly
- Restart browser if issues appear
- Disable unused browser extensions
- Keep OS updated

---

## 🚀 Back to Normal

After fixing:
1. Hard refresh page: `Ctrl+Shift+R`
2. Click microphone button
3. Allow microphone permission if asked
4. Speak clearly: "Hello"
5. Should see text appear
6. AI should respond with speech

---

## 📚 Additional Resources

- **VOICE_GUIDE.md** - Complete voice feature guide
- **COMPLETE_FEATURES_GUIDE.md** - All features explained
- Browser Speech Recognition docs: https://www.w3.org/TR/speech-api/

---

**Last Updated:** January 12, 2026

Still having issues? Check the browser console (F12) for detailed error messages.
