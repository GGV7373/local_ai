# Network Error Fix - Voice Feature Debugging

## 🔴 Issue Found
Your voice feature is showing: **"Network error. Check your connection."**

This typically means the Web Speech API cannot reach Google's speech recognition servers.

---

## ✅ Improvements Made

### 1. **Enhanced Error Messages**
- More descriptive error messages for different error types
- Better guidance for each error scenario
- Console logging for debugging

### 2. **Better Error Handling**
- Added try-catch blocks in voice initialization
- Retry mechanism if recognition starts twice
- Graceful fallback for failures

### 3. **Added Debugging Tools**
- Improved console logging
- Created diagnostic HTML page
- Better error tracking

### 4. **New Troubleshooting Guide**
- `VOICE_TROUBLESHOOTING.md` with step-by-step fixes
- Common solutions for network errors
- Advanced diagnostic steps

---

## 🚀 To Test the Fix

### Option 1: Quick Test in App
1. Open the app
2. Click the 🎤 microphone button
3. Speak: "Hello"
4. Check if it works now

### Option 2: Use Diagnostic Tool
1. Open browser and go to: `http://localhost:8000/static/voice-diagnostic.html`
2. Run all 4 tests
3. See detailed results
4. This identifies which part isn't working

### Option 3: Check Browser Console
1. Press `F12` to open Developer Tools
2. Click "Console" tab
3. Try the voice feature
4. Look for messages in red (errors)
5. Note down any error codes

---

## 🔍 Most Likely Causes

### 1. **Network/Internet Problem**
- **Sign:** "Network error"
- **Fix:** Check if you can browse normally (google.com loads)
- **Test:** Use diagnostic tool "Test Connection" button

### 2. **Firewall Blocking Speech Service**
- **Sign:** "Network error" + network seems fine elsewhere
- **Fix:** Check firewall settings or use VPN
- **Note:** Corporate networks often block this

### 3. **Microphone Permission Not Given**
- **Sign:** "Microphone not found" error
- **Fix:** Allow microphone in browser settings
- **Steps:** Browser → Settings → Microphone → Allow

### 4. **Browser Cache Issues**
- **Sign:** Random network errors
- **Fix:** Hard refresh (Ctrl+Shift+R)
- **Alternative:** Clear browser cache completely

### 5. **Wrong Language Settings**
- **Sign:** Works sometimes, fails sometimes
- **Fix:** Check language dropdown (English vs Norwegian)
- **Test:** Try both languages with diagnostic tool

---

## 📋 Step-by-Step Fix Guide

### Step 1: Verify Internet Works
```
In browser (any tab):
1. Go to https://google.com
2. Should load normally
3. If not, fix your internet connection
```

### Step 2: Clear Cache and Restart
```
1. Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
2. Select "All time"
3. Click "Clear data"
4. Close ALL browser tabs
5. Reopen the app
6. Try voice again
```

### Step 3: Check Microphone Permissions
```
Chrome/Edge:
1. Click lock icon next to URL
2. Find "Microphone"
3. Change to "Allow"
4. Reload page

Firefox:
1. Go to about:preferences#privacy
2. Find "Permissions" → "Microphone"
3. Click "Settings"
4. Ensure localhost is allowed

Safari:
1. System Preferences → Security & Privacy
2. Find "Microphone"
3. Ensure Safari is in list
4. Click allow if needed
```

### Step 4: Test with Diagnostic Tool
```
1. Go to: http://localhost:8000/static/voice-diagnostic.html
2. Click: "Test Browser Support"
3. Click: "Test Microphone"
4. Click: "Test Connection"
5. Click: "Start Speech Test" (speak something)
6. Check results - this tells you what's wrong
```

### Step 5: Try Different Browser
```
If failing in:
- Chrome → Try Edge
- Firefox → Try Chrome
- Safari → Try Edge
This identifies if it's browser-specific
```

---

## 💡 Network Error Specific Solutions

### For "Network error" message:

1. **Check Google Services are Reachable**
   ```javascript
   // In browser console (F12):
   fetch('https://www.google.com')
     .then(() => console.log('✅ Can reach Google'))
     .catch(() => console.log('❌ Cannot reach Google'))
   ```

2. **If Behind Corporate Firewall**
   - Ask IT to whitelist: `https://www.google.com/speech-api/`
   - Or connect to personal WiFi to test

3. **If Using VPN**
   - Try disabling VPN
   - Speech service sometimes blocks VPN traffic

4. **Check DNS**
   ```javascript
   // In console:
   console.log(navigator.onLine)  // Should be true
   ```

---

## 🛠️ Code Changes Made

### File: `gateway/static/app.js`

**Changes:**
1. Enhanced error messages (8 different error types now)
2. Added console logging for debugging
3. Added try-catch in `toggleVoiceInput()` function
4. Better recovery from recognition errors

**What This Helps:**
- More detailed error descriptions
- Console logs help identify real issue
- Automatic retry on failure
- Better handling of edge cases

---

## 📝 New Troubleshooting Resources

1. **VOICE_TROUBLESHOOTING.md**
   - Comprehensive troubleshooting guide
   - Step-by-step diagnostics
   - Common solutions

2. **voice-diagnostic.html**
   - Interactive diagnostic tool
   - Tests all 4 key systems
   - Visual pass/fail for each component

---

## ✨ After the Fix

Once working, you should:
1. Click 🎤 button
2. See "🎙️ Listening..." status
3. Speak clearly
4. See text appear in input
5. See AI respond with speech

---

## 📞 Still Having Issues?

Try these steps in order:

1. ✅ Run diagnostic tool (see all results)
2. ✅ Hard refresh (Ctrl+Shift+R)
3. ✅ Clear browser cache (Ctrl+Shift+Delete)
4. ✅ Try different browser
5. ✅ Restart computer
6. ✅ Try on different network
7. ✅ Check browser console errors (F12)

If still failing, your network or browser environment may not support cloud speech recognition. As a workaround:
- Use text input instead
- Upload audio files for transcription
- Use other features (export, documents, etc.)

---

## 🎯 Quick Reference

| Issue | Diagnostic | Fix |
|-------|-----------|-----|
| "Network error" | Test Connection button | Check internet or firewall |
| "No microphone" | Test Microphone button | Allow in browser permissions |
| "Browser doesn't support" | Test Browser Support button | Use Chrome, Edge, Safari, Firefox |
| "Speech not working" | Start Speech Test button | Check all above, then retry |

---

**Last Updated:** January 12, 2026

Use the diagnostic tool for fastest resolution! Go to:
`http://localhost:8000/static/voice-diagnostic.html`
