import os
import uuid
import shutil
import librosa
import soundfile as sf
from pydub import AudioSegment
from transformers import pipeline

# Use environment variable for cache, fallback to local directory
CACHE_DIR = os.environ.get("HF_HOME", "./hf_cache")
TEMP_DIR = "./temp_audio"
CONVERT_DIR = "./converted_audio"
MAX_CONVERTED_FILES = 10  # Reduced from 50 to save space

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CONVERT_DIR, exist_ok=True)

emotion_model = None

def get_emotion_model():
    global emotion_model
    if emotion_model is None:
        try:
            emotion_model = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-er",
                cache_dir=CACHE_DIR
            )
        except Exception as e:
            print(f"ERROR: Failed to load emotion model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e
    return emotion_model


def cleanup_old_converted_files():
    try:
        files = sorted(
            [os.path.join(CONVERT_DIR, f) for f in os.listdir(CONVERT_DIR)],
            key=os.path.getmtime
        )
        if len(files) > MAX_CONVERTED_FILES:
            for f in files[:-MAX_CONVERTED_FILES]:
                os.remove(f)
    except Exception as e:
        print(f"Cleanup warning: {e}")


def convert_to_wav(file_path):

    if file_path.lower().endswith(".wav"):
        return file_path

    try:
        ffmpeg_path = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not ffmpeg_path:
            raise RuntimeError(
                "ffmpeg is required to convert non-WAV files like .m4a. "
                "Install ffmpeg and make sure it is on your PATH."
            )

        new_path = os.path.join(
            CONVERT_DIR,
            os.path.basename(file_path).rsplit(".", 1)[0] + ".wav"
        )

        cleanup_old_converted_files()
        audio = AudioSegment.from_file(file_path)
        audio.export(new_path, format="wav")

        return new_path

    except Exception as e:
        raise RuntimeError(f"Conversion failed: {e}") from e


def split_audio(file_path, chunk_size=5):

    y, sr = librosa.load(file_path, sr=None)

    duration = librosa.get_duration(y=y, sr=sr)

    parts = []

    for i in range(0, int(duration), chunk_size):
        parts.append((i, min(i + chunk_size, duration)))

    return parts, y, sr


def detect_emotion(audio_file):
    model = get_emotion_model()
    result = model(audio_file)
    return result[0]["label"]


def analyze_audio(file_path):
    file_path = convert_to_wav(file_path)

    parts, y, sr = split_audio(file_path)

    emotions = []
    last_emotion = None
    emotion_start_time = 0

    for start, end in parts:
        temp_name = f"{uuid.uuid4().hex}.wav"
        temp_path = os.path.join(TEMP_DIR, temp_name)

        try:
            clip = y[int(start * sr):int(end * sr)]
            sf.write(temp_path, clip, sr)
            emotion = detect_emotion(temp_path)

            # only log when emotion changes
            if emotion != last_emotion:
                if last_emotion is not None:
                    minutes = int(emotion_start_time) // 60
                    seconds = int(emotion_start_time) % 60
                    emotions.append({
                        "time": f"{minutes}:{seconds:02d}",
                        "emotion": last_emotion,
                        "duration": f"{int(start - emotion_start_time)}s"
                    })

                last_emotion = emotion
                emotion_start_time = start

        except Exception as e:
            print("Chunk error:", e)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if last_emotion is not None:
        minutes = int(emotion_start_time) // 60
        seconds = int(emotion_start_time) % 60
        total_duration = parts[-1][1] - emotion_start_time
        emotions.append({
            "time": f"{minutes}:{seconds:02d}",
            "emotion": last_emotion,
            "duration": f"{int(total_duration)}s"
        })

    # Clean up uploaded and converted files after processing to save space
    cleanup_uploads()
    
    return emotions if emotions else [{"time": "0:00", "emotion": "unknown", "duration": "0s"}]


def cleanup_uploads():
    """Remove old uploaded files to save disk space on Render"""
    try:
        upload_dir = "./uploads"
        if os.path.exists(upload_dir):
            files = sorted(
                [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))],
                key=os.path.getmtime
            )
            # Keep only the 5 most recent uploads
            if len(files) > 5:
                for f in files[:-5]:
                    try:
                        os.remove(f)
                        print(f"Cleaned up old upload: {f}")
                    except Exception as e:
                        print(f"Could not remove {f}: {e}")
    except Exception as e:
        print(f"Upload cleanup warning: {e}")
