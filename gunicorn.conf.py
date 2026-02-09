"""
Gunicorn configuration optimized for Render free tier (512 MB RAM).
"""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = 2048

# Worker processes - single worker for free tier memory constraints (512 MB)
workers = 1
worker_class = 'sync'
worker_connections = 10  # Low to limit concurrent requests
max_requests = 500  # Restart worker more frequently to prevent memory creep
max_requests_jitter = 25

# Timeouts - increased for model loading and audio processing
timeout = 240  # 4 minutes for processing up to 2-minute audio files
keepalive = 5

# Preload app to load model during startup, not on first request
# This reduces memory spike on first request
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'voice-emotion-detector'

def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 60)
    print("Gunicorn is starting (Render free tier optimized)")
    print(f"Workers: {workers} (free tier limit)")
    print(f"Timeout: {timeout}s (for audio processing)")
    print(f"Max RAM: 512 MB")
    print(f"Preload: {preload_app} (load model at startup)")
    print("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    print("=" * 60)
    print("Server is ready. Emotion model preloaded.")
    print("Ready to accept requests (max 2-minute audio files)")
    print("=" * 60)

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("=" * 60)
    print("Gunicorn is shutting down...")
    print("=" * 60)
