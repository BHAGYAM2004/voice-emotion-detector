#!/bin/bash
# Render deployment verification script
# This script checks for common deployment issues before starting the app

echo "=================================="
echo "RENDER DEPLOYMENT PRE-FLIGHT CHECK"
echo "=================================="

# Check Python version
echo -n "✓ Python version: "
python --version

# Check if ffmpeg is installed
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg: INSTALLED"
    ffmpeg -version | head -n 1
else
    echo "✗ FFmpeg: NOT FOUND (only WAV files will work)"
fi

# Check disk space
echo -n "✓ Disk space available: "
df -h . | tail -1 | awk '{print $4}'

# Check memory (if available)
if [ -f /proc/meminfo ]; then
    echo -n "✓ Total memory: "
    grep MemTotal /proc/meminfo | awk '{print $2/1024 " MB"}'
fi

# Verify cache directory
if [ -d "${HF_HOME:-./hf_cache}" ]; then
    echo "✓ Cache directory exists: ${HF_HOME:-./hf_cache}"
else
    echo "✗ Cache directory missing, creating: ${HF_HOME:-./hf_cache}"
    mkdir -p "${HF_HOME:-./hf_cache}"
fi

# Check if model cache exists
if [ -d "${HF_HOME:-./hf_cache}/models--superb" ]; then
    echo "✓ Model cache found (fast startup expected)"
    du -sh "${HF_HOME:-./hf_cache}/models--superb" 2>/dev/null || echo "✓ Model cache exists"
else
    echo "⚠ Model cache empty (first download ~500MB, may take 3-5 min)"
fi

# Test pip packages
echo -n "✓ Testing imports... "
python -c "import torch, transformers, librosa, flask" && echo "SUCCESS" || echo "FAILED"

echo "=================================="
echo "Pre-flight check complete!"
echo "=================================="
