from flask import Flask, render_template, request
import os
import pandas as pd
import plotly.express as px
from werkzeug.utils import secure_filename
from emotion import analyze_audio

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

        path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(path)

        try:
            data = analyze_audio(path)
        except Exception as e:
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
