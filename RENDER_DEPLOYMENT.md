# Render Deployment Guide

## Overview
This voice emotion detector has been optimized to run on Render's free tier with space limitations (~512MB build size).

## Key Optimizations Made

### 1. CPU-Only PyTorch
- **Before**: Full PyTorch with CUDA support (~800MB-1GB)
- **After**: CPU-only PyTorch wheels (~200-300MB)
- **Version**: 2.6.0+ with security patches
- **Impact**: 60-70% reduction in package size

### 2. Security Updates
- **PyTorch**: Updated to 2.6.0 to address:
  - Heap buffer overflow vulnerability
  - Use-after-free vulnerability
  - Remote code execution via torch.load
- **Transformers**: Updated to 4.48.0 to address:
  - Multiple deserialization of untrusted data vulnerabilities

### 3. Custom Build Command
The `render.yaml` now uses a custom build command that:
- Explicitly installs CPU-only PyTorch from the CPU wheel index
- Uses patched versions with security fixes (PyTorch 2.6.0, Transformers 4.48.0)
- Installs only essential dependencies
- Uses specific versions to ensure compatibility

### 4. Automatic File Cleanup
Added automatic cleanup functions to manage disk space:
- **Upload cleanup**: Keeps only 5 most recent uploaded files
- **Converted files**: Maintains max 10 converted audio files
- **Temp files**: Immediate cleanup after processing each chunk

### 5. Model Cache Configuration
- Uses environment variables (`HF_HOME`, `TRANSFORMERS_CACHE`)
- Points to Render's persistent storage path
- Model downloaded once, cached for all subsequent requests

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Optimized for Render deployment"
   git push origin main
   ```

2. **Create Render Service**
   - Go to https://render.com/dashboard
   - Click "New +" → "Web Service"
   - Select your GitHub repository
   - Render will auto-detect `render.yaml`
   - Click "Create Web Service"

3. **Wait for Build** (10-15 minutes first time)
   - Installing CPU-optimized dependencies
   - Setting up FFmpeg
   - Model will download on first request

4. **First Request**
   - The first audio analysis will take 2-3 minutes (model download)
   - Subsequent requests will be fast (model cached)

## Expected Deployment Size

- **Build**: ~500-600MB (within free tier limit)
- **Model cache**: ~380MB (one-time download)
- **Runtime**: ~200-300MB memory usage

## Troubleshooting

### Build Fails with "Out of Disk Space"
- Ensure you're using the latest `render.yaml` with CPU-only PyTorch
- Check that the build command installs from `https://download.pytorch.org/whl/cpu`

### Model Download Fails
- This happens on first request, not during build
- Check Render logs: Dashboard → Your Service → Logs
- Model will retry on next request

### Application Crashes After Some Time
- Free tier has 512MB RAM limit
- Our optimizations should keep it under this
- If crashes persist, consider upgrading to paid tier

### Files Accumulate Over Time
- Automatic cleanup runs after each analysis
- Manually trigger cleanup by redeploying (restarts the service)

## Monitoring

Check these endpoints to monitor your service:
- `/health` - Basic health check (returns "OK")
- `/warmup` - Confirms server and model are ready
- Render Dashboard → Logs - View real-time application logs

## Cost Considerations

**Free Tier Limits:**
- 512MB RAM
- 750 hours/month (goes to sleep after 15 min inactivity)
- First request after sleep takes 30-60s to wake up

**When to Upgrade:**
- Need 24/7 uptime without sleep
- Need more than 512MB RAM
- High traffic volume (>750 hours/month)

## Auto-Deployment

Since the repository is linked to GitHub:
- Any push to `main` branch triggers automatic redeployment
- Build takes 5-10 minutes
- Service automatically switches to new version after successful build
- Zero downtime deployment

## Performance Tips

1. **Keep the service warm**: Use a service like UptimeRobot to ping `/warmup` every 14 minutes
2. **First request**: Warn users that first request may take 2-3 minutes
3. **File size**: Recommend users upload files under 2 minutes for faster processing
4. **Format**: WAV files process fastest (no conversion needed)

## Security Notes

- Uploaded files are cleaned up automatically
- No persistent user data stored
- All processing happens server-side
- Model cache is read-only after initial download

## Support

For issues specific to:
- **Render deployment**: Check Render docs or community forum
- **Application code**: Open issue on GitHub repository
- **Model/ML issues**: Check Hugging Face model card for `superb/wav2vec2-base-superb-er`
