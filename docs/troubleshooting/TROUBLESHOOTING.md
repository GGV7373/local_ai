# Troubleshooting Guide

Common issues and solutions for Nora AI.

---

## 📖 Table of Contents

- [Voice Features](#-voice-features)
- [Network & Connection](#-network--connection)
- [Audio & Transcription](#-audio--transcription)
- [File Upload](#-file-upload)
- [Deployment](#-deployment)
- [Diagnostics](#-diagnostics)

---

## 🎤 Voice Features

### Network Error While Testing Voice

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

**3. Check Microphone Permissions**
- Browser asks for microphone access the first time
- Make sure you clicked **"Allow"** in the permission popup
- If you clicked "Block":
  - Chrome/Edge: Click lock icon in address bar → allow microphone
  - Firefox: Settings → Privacy → Permissions → Microphone
  - Safari: System Preferences → Security & Privacy → Microphone

**4. Close Other Tabs Using Microphone**
- Other apps/tabs using microphone can interfere
- Close video calls, recording apps, etc.
- Try voice feature again

**5. Try a Different Browser**
- Chrome ✅ (best support)
- Edge ✅ (best support)
- Firefox ✅ (works well)
- Safari ✅ (works well)

### Common Voice Issues

#### "No speech detected"
- Check that your microphone is working
- Speak clearly and loud enough
- Make sure you're in a quiet environment
- Try again - sometimes it needs a moment to listen

#### "Permission denied"
- Allow microphone access when the browser asks
- Check your browser settings
- Some firewalls may block microphone access

#### Speech recognition not available
- Use a modern browser (Chrome, Edge, Safari, Firefox)
- Older browsers don't support Web Speech API
- Try a different browser if one doesn't work

#### Speech sounds robotic or unclear
- This depends on your browser's built-in voice
- Different browsers have different voice quality
- Try adjusting your browser's voice settings

---

## 🌐 Network & Connection

### Advanced Network Troubleshooting

#### Check Browser Console for Details
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

### Step-by-Step Diagnostic

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

### Firewall/Proxy Solutions

If your network blocks speech recognition:

**Option 1: Use Text Input**
The application works perfectly with text input when voice is unavailable.

**Option 2: Contact IT Department**
Ask them to whitelist the speech recognition service endpoint.

**Option 3: Use Different Network**
Try from a personal device on a different network to verify the issue.

---

## 🎵 Audio & Transcription

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

---

## 📁 File Upload

### Common File Upload Issues

#### "File type not supported"
- Check file extension is allowed
- See configuration for allowed extensions
- Ensure file is not corrupted

#### Upload fails or times out
- Check file size (limit may apply)
- Verify internet connection is stable
- Try uploading a smaller file first
- Check browser console for errors

#### File uploads but not visible
- Refresh the files list
- Check you're in the correct tab
- Verify authentication token is valid
- Check server logs for errors

---

## 🚀 Deployment

### HTTPS Setup Issues

#### "Connection refused"
```bash
# Check if nginx is running
sudo systemctl status nginx

# Start if not running
sudo systemctl start nginx

# Check port 443 is open
sudo netstat -tlnp | grep 443
```

#### "Certificate error" in browser
This is normal for self-signed certs. Click through the warning.

#### "Port already in use"
```bash
# Find what's using the port
sudo lsof -i :443

# Kill if needed
sudo kill -9 <PID>
```

#### Voice features not working after HTTPS setup
1. Verify HTTPS is working: `https://YOUR_IP`
2. Run diagnostic tool: `https://YOUR_IP/static/voice-diagnostic.html`
3. Check browser console (F12) for errors
4. Verify microphone permissions
5. See [Voice Features](#-voice-features) section above

#### Nginx not starting
```bash
# Check configuration
docker exec nora_nginx nginx -t

# View detailed logs
docker-compose logs nginx

# Common issues:
# - Certificate files missing
# - Port conflicts
# - Configuration syntax errors
```

### Docker Issues

#### Containers won't start
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs

# Restart specific service
docker-compose restart gateway
```

#### Port conflicts
```bash
# Check what's using the port
sudo lsof -i :8765
sudo lsof -i :443

# Stop conflicting service or change port in docker-compose.yml
```

#### Permission denied errors
```bash
# Fix ownership
sudo chown -R $USER:$USER ./uploads ./nginx/ssl

# Set proper permissions
chmod 755 ./uploads
chmod 644 ./nginx/ssl/*
```

---

## 🧪 Diagnostics

### Diagnostic Tool

For comprehensive testing, visit:
```
https://YOUR_SERVER_IP/static/voice-diagnostic.html
```

or for local testing:
```
http://localhost:8000/static/voice-diagnostic.html
```

This tool tests:
- Browser support for Speech Recognition
- Microphone access
- Internet connection
- Speech recognition service availability

### Manual Diagnostic Steps

#### Test Backend is Running
```bash
curl http://localhost:8765/health
```
Should return status information.

#### Test HTTPS Access
```bash
curl -k https://localhost:443
```
Should return HTML content.

#### Check Logs

**Docker logs:**
```bash
docker-compose logs -f gateway
docker-compose logs -f nginx
```

**Nginx logs:**
```bash
docker-compose exec nginx tail -f /var/log/nginx/error.log
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Common Error Codes

| Error Code | Meaning | Solution |
|------------|---------|----------|
| 401 | Unauthorized | Check authentication token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check URL path |
| 500 | Server Error | Check server logs |
| 502 | Bad Gateway | Gateway not responding |
| 503 | Service Unavailable | Service down |

---

## 🔧 Quick Fixes Summary

### Voice Issues
1. Hard refresh browser
2. Check microphone permissions
3. Test internet connection
4. Try different browser
5. Run diagnostic tool

### Network Issues
1. Check internet connectivity
2. Verify firewall settings
3. Test with diagnostic tool
4. Check browser console
5. Try different network

### Deployment Issues
1. Verify all services running
2. Check SSL certificates exist
3. Review nginx configuration
4. Check firewall ports open
5. Review docker logs

### File Issues
1. Check file format supported
2. Verify file size within limits
3. Check permissions
4. Review server logs
5. Test with smaller file

---

## 📞 Additional Resources

- [Voice Features](../features/VOICE.md) - Voice setup and configuration
- [Audio & Export](../features/AUDIO_EXPORT.md) - Audio transcription and export
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Server setup
- [Features Guide](../FEATURES.md) - Complete feature documentation

### External Resources
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Still having issues?** Check the diagnostic tool or review the detailed guides linked above.
