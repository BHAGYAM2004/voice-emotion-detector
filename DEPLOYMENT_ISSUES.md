# RENDER DEPLOYMENT: EXPECTED ISSUES & SOLUTIONS

## 🔴 CRITICAL ISSUES (Will Cause Deployment Failure)

### 1. **Model Download Timeout During First Deploy**
**Problem:** Model (~500MB) downloads during first build/startup
**Symptoms:** Build takes >15 minutes, timeout errors
**Prevention:** ✅ Already handled via `preload_app=True` in gunicorn config
**Solution if it happens:**
- Render will cache the model after first successful deploy
- Subsequent deploys will be fast (~2-3 minutes)
- If timeout persists, temporarily increase timeout in gunicorn.conf.py to 600s

### 2. **Memory Exhaustion (OOM Killed)**
**Problem:** App uses >512 MB RAM
**Symptoms:** "Worker was sent SIGKILL! Perhaps out of memory?"
**Prevention:** ✅ Already handled:
- 30 MB max file size
- 2-minute max audio duration
- Aggressive garbage collection
- 1 worker only
**Solution if it happens:**
- Reduce MAX_AUDIO_DURATION to 60 seconds in app.py
- Reduce max file size to 15 MB
- Last resort: Upgrade to Starter plan ($7/mo = 1GB RAM)

### 3. **Python 3.13 Used Instead of 3.11**
**Problem:** Render ignores version spec, uses 3.13, packages fail to build
**Symptoms:** "error: metadata-generation-failed", pandas compilation errors
**Prevention:** ✅ Already handled:
- .python-version file created
- runtime.txt specifies 3.11.10
- render.yaml has PYTHON_VERSION env var
**Solution if it happens:**
- In Render dashboard → Settings → Environment
- Add/verify: PYTHON_VERSION=3.11.10
- Clear build cache and redeploy

---

## 🟡 MODERATE ISSUES (May Cause Instability)

### 4. **FFmpeg Not Installed**
**Problem:** apt package fails to install
**Symptoms:** "ffmpeg is required to convert non-WAV files"
**Prevention:** ✅ Checked in emotion.py at startup
**Solution:**
- Check Render logs for "FFmpeg detected"
- If missing, only accept WAV files temporarily
- Add to render.yaml: `buildCommand: apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`

### 5. **Cold Start After 15-Minute Inactivity**
**Problem:** Free tier sleeps, first request after wake is slow
**Symptoms:** First request takes 30-60 seconds
**Prevention:** ⚠️ Unavoidable on free tier
**Workaround:**
- Set up external ping service (UptimeRobot, cron-job.org)
- Ping /health endpoint every 10 minutes
- Keeps service awake 24/7

### 6. **Disk Space Full from Cached Files**
**Problem:** Model cache + uploads + temp files fill disk
**Symptoms:** "No space left on device"
**Prevention:** ✅ Already handled:
- Cleanup functions for uploads (keep 5)
- Cleanup for converted files (keep 10)
- Temp files deleted after each request
**Monitor:** Check Render logs for cleanup messages

### 7. **Concurrent Request Overload**
**Problem:** Multiple users upload simultaneously
**Symptoms:** Requests queue up, timeouts
**Prevention:** ✅ Already handled:
- 1 worker only (serializes requests)
- worker_connections=10 (limits concurrent)
**User Impact:** Users may wait in queue during high traffic

---

## 🟢 MINOR ISSUES (Warnings, Non-Critical)

### 8. **Pydub Syntax Warnings**
**Problem:** Invalid escape sequences in pydub library
**Symptoms:** SyntaxWarning messages in logs
**Prevention:** ⚠️ External library bug, not fixable
**Impact:** None - just warnings, functionality works fine

### 9. **Build Cache Misses**
**Problem:** Render doesn't restore cache, rebuilds everything
**Symptoms:** Build takes 10-15 minutes instead of 2-3
**Prevention:** None (Render's decision)
**Impact:** Longer deploy time, but app works fine

### 10. **Heroku-style runtime.txt Ignored**
**Problem:** Render might use PYTHON_VERSION env var instead
**Symptoms:** "Using Python version 3.13.4 (default)"
**Prevention:** ✅ Multiple fallbacks in place
**Solution:** Update render.yaml PYTHON_VERSION env var

---

## 📊 DEPLOYMENT SUCCESS CHECKLIST

After deployment, verify in Render logs:

```
✅ "Using Python version 3.11" (not 3.13)
✅ "FFmpeg detected and available"
✅ "Loading emotion model..."
✅ "✓ Emotion model loaded successfully"
✅ "✓ Application ready to serve requests"
✅ "Server is ready. Emotion model preloaded."
✅ "[INFO] Listening at: http://0.0.0.0:10000"
✅ No "WORKER TIMEOUT" messages
✅ No "SIGKILL" messages
```

---

## 🚀 POST-DEPLOYMENT TESTING

### Test 1: Health Check
```bash
curl https://your-app.onrender.com/health
# Should return: {"status":"ok","model_loaded":true}
```

### Test 2: Warmup
```bash
curl https://your-app.onrender.com/warmup
# Should return: {"status":"ready","model_loaded":true}
```

### Test 3: Small Audio File (<30s)
- Upload a short WAV file via web UI
- Should complete in 10-30 seconds

### Test 4: Maximum Duration (2 minutes)
- Upload a 2-minute audio file
- Should complete in 60-120 seconds
- Watch memory in logs

### Test 5: Oversized File (>30 MB)
- Should reject with "File too large" message

### Test 6: Over-Duration File (>2 minutes)
- Should reject with "Audio too long" message

---

## 🔧 IF ALL ELSE FAILS

1. **Enable debug logging:**
   - Add to render.yaml envVars: `DEBUG=true`
   - Redeploy

2. **Reduce limits aggressively:**
   ```python
   MAX_AUDIO_DURATION = 45  # 45 seconds
   MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB
   ```

3. **Use smaller model (experimental):**
   Replace in emotion.py:
   ```python
   model="facebook/wav2vec2-base-960h"  # Smaller, but less accurate
   ```

4. **Last resort - Upgrade plan:**
   - Render Starter: $7/month
   - 1 GB RAM (2x free tier)
   - No sleep/cold starts
   - Much more reliable

---

## 📞 SUPPORT RESOURCES

- Render Docs: https://render.com/docs/free#free-web-services
- Troubleshooting: https://render.com/docs/troubleshooting-deploys
- Free tier limits: https://render.com/docs/free#free-web-services
- Community: https://community.render.com/

---

Generated for Render deployment optimized for 512 MB free tier.
