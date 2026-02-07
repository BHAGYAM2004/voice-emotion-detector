# Voice Emotion Detector

A Flask-based web application that analyzes voice recordings to detect emotional changes in real-time. Uses AI-powered emotion recognition to identify when emotions transition during speech.

## Features

- 🎤 **Audio Upload** - Support for WAV, MP3, M4A, FLAC, OGG formats
- 🤖 **AI Emotion Detection** - WAV2Vec2 transformer model for accurate emotion recognition
- 📊 **Real-time Timeline** - Tracks emotion changes with exact timestamp and duration
- 📈 **Interactive Charts** - Plotly visualization of emotional journey
- 🎨 **Glass Morphism UI** - Modern, professional interface with smooth animations
- ⚡ **Fast Processing** - Processes 5-second audio chunks in parallel
- 🔄 **Format Conversion** - Auto-converts M4A and other formats to WAV using FFmpeg

## Detected Emotions

- Happy
- Sad
- Angry
- Neutral
- Surprised
- Fearful
- Disgusted

## Setup

### Requirements

- Python 3.11+
- FFmpeg (for audio conversion)
- 8GB RAM minimum
- 15GB disk space (for ML models)

### Local Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR-USERNAME/voice-emotion-detector.git
cd voice-emotion-detector
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install FFmpeg:**

**Windows:**
- Download from https://ffmpeg.org/download.html
- Extract to `C:\ffmpeg`
- Add `C:\ffmpeg\bin` to system PATH environment variable
- Restart terminal/IDE

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

5. **Run the app:**
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Usage

1. **Upload Audio:**
   - Click "Choose or drag audio file"
   - Select a WAV, MP3, M4A, FLAC, or OGG file
   - Click "Analyze Now"

2. **View Results:**
   - See emotion timeline table with transitions
   - View interactive chart showing emotional journey
   - Print or export the report

## API Endpoints

- `GET /` - Home page (upload form)
- `POST /` - Process audio upload
- `GET /health` - Health check
- `GET /warmup` - Server warmup (Render)

## Project Structure

```
voice-emotion-detector/
├── app.py                 # Flask application
├── emotion.py             # Emotion detection logic
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version (3.11)
├── render.yaml           # Render deployment config
├── .gitignore            # Git ignore rules
├── templates/
│   ├── index.html        # Upload page
│   └── result.html       # Results page
├── static/
│   └── chart.html        # Generated charts
├── uploads/              # Uploaded audio files
├── temp_audio/           # Temporary chunks
└── converted_audio/      # Converted WAV files
```

## How It Works

1. **Upload** - User uploads audio file
2. **Convert** - App converts to WAV if needed (using FFmpeg + Pydub)
3. **Split** - Audio divided into 5-second chunks
4. **Analyze** - Each chunk processed by WAV2Vec2 emotion model
5. **Track Changes** - Only records emotion transitions (not every chunk)
6. **Visualize** - Creates timeline table and Plotly chart
7. **Display** - Results shown with time, emotion, and duration

## Deployment

### Deploy to Render

1. **Push to GitHub:**
```bash
git remote add origin https://github.com/YOUR-USERNAME/voice-emotion-detector.git
git branch -M main
git push -u origin main
```

2. **Connect to Render:**
   - Go to https://render.com
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Render auto-detects `render.yaml`
   - Click "Create Web Service"

3. **Wait for deployment** (5-10 minutes)
   - Render builds the image
   - Installs FFmpeg
   - Downloads ML models
   - Deploys app

Once deployed, your public URL will be displayed!

## Performance Tips

- Shorter files process faster (< 2 minutes)
- Use WAV for instant processing (no conversion needed)
- M4A files require FFmpeg conversion (adds ~5 seconds)
- Model caches on first run, subsequent uploads are faster

## Troubleshooting

### FFmpeg Not Found
- **Windows:** Ensure `C:\ffmpeg\bin` is in system PATH
- **Mac/Linux:** Run `which ffmpeg` to verify installation
- Restart terminal/IDE after adding to PATH

### Model Download Fails
- Requires internet connection
- Models cached in `./hf_cache/` (3GB+)
- Check disk space

### Audio Processing Fails
- Ensure file is valid audio
- Try converting to WAV first
- Check file is under 500MB

### Permission Errors on Render
- Check logs with `render logs`
- Verify `render.yaml` configuration
- Ensure repo is public or Render has access

## Technologies Used

- **Flask** - Web framework
- **PyTorch** - Deep learning
- **Transformers** - WAV2Vec2 emotion model
- **Librosa** - Audio processing
- **Pydub** - Audio file conversion
- **Plotly** - Interactive charts
- **FFmpeg** - Audio codec support

## License

MIT License - Feel free to use for educational purposes.

## Support

For issues or questions, check:
- GitHub Issues
- Render Docs: https://render.com/docs
- Flask Docs: https://flask.palletsprojects.com/

---

**Built with ❤️ for emotion detection**
