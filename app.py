from flask import Flask, render_template, request, jsonify
import os
import sys
import gc
import pandas as pd
import plotly.express as px
from werkzeug.utils import secure_filename
from emotion import analyze_audio, get_emotion_model

app = Flask(__name__)

# Configure for Render free tier (512 MB memory limit)
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB max file upload
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
MAX_AUDIO_DURATION = 120  # Max 2 minutes (120 seconds) to prevent memory overload
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)  # Ensure static directory exists

# Track startup status
model_loaded = False
startup_error = None
model_optimization_method = None

# Preload the model when app starts (important for gunicorn preload_app=True)
print("="*60)
print("RENDER DEPLOYMENT: Starting application...")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print("Memory Optimization Strategies Enabled:")
print("  ✓ Option 1: ONNX Runtime (60% smaller than PyTorch)")
print("  ✓ Option 3: Lightweight PyTorch Model")
print("  ✓ Option 4: Dynamic Quantization (30-40% reduction)")
print("="*60)

print("Preloading emotion detection model...")
try:
    model = get_emotion_model()
    model_loaded = True
    
    # Import to get model type info
    from emotion import model_type
    model_optimization_method = model_type
    print(f"✓ Model preloaded successfully! (Using: {model_type})")
    print("✓ Application ready to serve requests")
    
    # Aggressive initial garbage collection
    gc.collect()
    print("✓ Garbage collection completed")
    
except Exception as e:
    startup_error = str(e)
    print(f"✗ Warning: Could not preload model: {e}")
    print("✗ Model will be loaded on first request instead (may cause timeout)")
    print("="*60)

@app.template_filter('unique_emotions')
def unique_emotions_filter(data):
    return len(set(item['emotion'] for item in data))

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        file = request.files["audio"]

        if not file or file.filename == "":
            return "No file uploaded"

        filename = secure_filename(file.filename)
        if not filename or not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return "Invalid file type. Supported: wav, mp3, m4a, flac, ogg"

        # Check file size before saving
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return f"File too large. Maximum: 30 MB, received: {file_size / 1024 / 1024:.1f} MB"

        path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(path)

        try:
            data = analyze_audio(path, max_duration=MAX_AUDIO_DURATION)
        except ValueError as e:
            # Clean up on validation error
            try:
                os.remove(path)
            except:
                pass
            return str(e)
        except Exception as e:
            # Clean up on any error
            try:
                os.remove(path)
            except:
                pass
            return f"Audio processing failed: {e}"
        
        df = pd.DataFrame(data)

        fig = px.line(
            df,
            x="time",
            y="emotion",
            title="Emotion Timeline"
        )

        fig.write_html("static/chart.html")
        
        # Aggressive memory cleanup after processing
        gc.collect()  # Collect garbage
        del df  # Delete dataframe
        del fig  # Delete figure
        gc.collect()  # Collect again

        return render_template("result.html", data=data)

    return render_template("index.html")


@app.route("/warmup")
def warmup():
    """Warmup endpoint to wake up sleeping service and verify model is loaded."""
    try:
        model = get_emotion_model()
        return jsonify({
            "status": "ready",
            "model_loaded": model is not None,
            "message": "Server is warm and model loaded"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "model_loaded": False,
            "error": str(e)
        }), 500

@app.route("/health")
def health():
    """Health check endpoint for Render monitoring."""
    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "model_optimization": model_optimization_method,
        "memory_strategies": {
            "onnx_runtime": "Option 1 - 60% size reduction",
            "lightweight_pytorch": "Option 3 - Smaller model",
            "quantization": "Option 4 - 30-40% size reduction"
        },
        "startup_error": startup_error,
        "limits": {
            "max_file_size_mb": 30,
            "max_duration_seconds": MAX_AUDIO_DURATION,
            "render_memory_mb": 512
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
