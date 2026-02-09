from flask import Flask, render_template, request
import os
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

# Preload the model when app starts (important for gunicorn preload_app=True)
print("Preloading emotion detection model...")
try:
    get_emotion_model()
    print("Model preloaded successfully!")
except Exception as e:
    print(f"Warning: Could not preload model: {e}")
    print("Model will be loaded on first request instead.")

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

        return render_template("result.html", data=data)

    return render_template("index.html")


@app.route("/warmup")
def warmup():
    return "Server is warm and model loaded."

@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
