"""
Gunicorn configuration optimized for Render free tier.
"""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = 2048

# Worker processes - use only 1 worker for free tier memory constraints
workers = 1
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000  # Restart worker after 1000 requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Timeouts
timeout = 180  # 3 minutes - allows time for model loading on first request
keepalive = 5

# Preload app to load model during startup, not on first request
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
    print("Gunicorn is starting...")
    print(f"Workers: {workers}")
    print(f"Timeout: {timeout}s")
    print(f"Preload: {preload_app}")
    print("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    print("=" * 60)
    print("Server is ready. Preloading emotion model...")
    print("=" * 60)

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("=" * 60)
    print("Gunicorn is shutting down...")
    print("=" * 60)
