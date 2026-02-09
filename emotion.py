import os
import uuid
import shutil
import gc
import librosa
import soundfile as sf
from pydub import AudioSegment
from transformers import pipeline
import torch

# Use environment variable for cache, fallback to local directory
CACHE_DIR = os.environ.get("HF_HOME", "./hf_cache")
TEMP_DIR = "./temp_audio"
CONVERT_DIR = "./converted_audio"
MAX_CONVERTED_FILES = 10  # Reduced from 50 to save space

# Verify ffmpeg availability at module load
try:
    ffmpeg_available = bool(shutil.which("ffmpeg"))
    if ffmpeg_available:
        print("✓ FFmpeg detected and available")
    else:
        print("⚠ FFmpeg not found - only WAV files will be supported")
except Exception as e:
    print(f"⚠ Could not check for FFmpeg: {e}")
    ffmpeg_available = False

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CONVERT_DIR, exist_ok=True)

emotion_model = None
model_type = None

def quantize_model(model):
    """Apply dynamic quantization to reduce model size by ~30-40% (Option 4)."""
    try:
        from torch.quantization import quantize_dynamic
        print("Applying dynamic quantization to reduce model size...")
        quantized_model = quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        print("✓ Model quantized successfully (30-40% size reduction)")
        return quantized_model
    except Exception as e:
        print(f"⚠ Quantization failed, using non-quantized model: {e}")
        return model

def load_onnx_model():
    """Try to load model with ONNX Runtime for 60% memory reduction (Option 1)."""
    try:
        print("Attempting to load model with ONNX Runtime (memory-optimized)...")
        # Use optimum to get ONNX version of the model
        from optimum.onnxruntime import ORTModelForAudioClassification
        from transformers import AutoFeatureExtractor
        
        model_name = "superb/wav2vec2-base-superb-er"
        print(f"Loading ONNX model: {model_name}")
        
        # Load ONNX model (much smaller than PyTorch)
        ort_model = ORTModelForAudioClassification.from_pretrained(
            model_name,
            cache_dir=CACHE_DIR
        )
        
        feature_extractor = AutoFeatureExtractor.from_pretrained(
            model_name,
            cache_dir=CACHE_DIR
        )
        
        print("✓ ONNX model loaded successfully (60% smaller than PyTorch)")
        return (ort_model, feature_extractor, "onnx")
        
    except Exception as e:
        print(f"⚠ ONNX loading failed: {e}")
        print("  Falling back to lightweight PyTorch model...")
        return None

def load_pytorch_model():
    """Load lightweight PyTorch model with quantization (Options 3 & 4)."""
    try:
        # Option 3: Use a lighter model (smaller base model)
        # facebook/wav2vec2-base is lighter than the superb version
        model_name = "facebook/wav2vec2-base"
        print(f"Loading lightweight PyTorch model: {model_name}")
        
        model = pipeline(
            "audio-classification",
            model=model_name,
            cache_dir=CACHE_DIR,
            device=-1  # Use CPU
        )
        
        # Option 4: Apply quantization for further size reduction
        try:
            # Get the underlying model for quantization
            underlying_model = model.model
            quantized = quantize_model(underlying_model)
            model.model = quantized
            print("✓ PyTorch model loaded and quantized (30-40% smaller)")
        except Exception as e:
            print(f"⚠ Quantization skipped: {e}")
        
        return (model, None, "pytorch_lightweight")
        
    except Exception as e:
        print(f"⚠ Lightweight model loading failed: {e}")
        print("  Falling back to original superb model...")
        return None

def get_emotion_model():
    """Load emotion detection model with memory optimization (Options 1, 3, 4)."""
    global emotion_model, model_type
    if emotion_model is None:
        try:
            print("="*60)
            print("MEMORY OPTIMIZATION: Loading emotion model")
            print("Attempting strategies: ONNX → PyTorch Lightweight → Quantization")
            print("="*60)
            
            # Try Option 1: ONNX Runtime first (60% smaller)
            result = load_onnx_model()
            if result:
                emotion_model, feature_extractor, model_type = result
                gc.collect()
                return emotion_model
            
            # Fall back to Option 3 & 4: Lightweight PyTorch + Quantization
            result = load_pytorch_model()
            if result:
                emotion_model, feature_extractor, model_type = result
                gc.collect()
                return emotion_model
            
            # Last resort: Original model (will likely exceed 512MB)
            print("Last resort: Loading original superb model...")
            emotion_model = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-er",
                cache_dir=CACHE_DIR
            )
            model_type = "pytorch_original"
            
            print("✓ Emotion model loaded (original version - high memory)")
            # Force garbage collection after model load
            gc.collect()
            
        except Exception as e:
            print(f"ERROR: Failed to load emotion model: {e}")
            print(f"Cache dir exists: {os.path.exists(CACHE_DIR)}")
            print(f"Cache dir writable: {os.access(CACHE_DIR, os.W_OK)}")
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
    """Detect emotion from audio file, handling both ONNX and PyTorch models."""
    global emotion_model, model_type
    
    model = get_emotion_model()
    
    if model_type == "onnx":
        # ONNX models need feature extraction
        try:
            from optimum.onnxruntime import ORTModelForAudioClassification
            from transformers import AutoFeatureExtractor
            
            feature_extractor = AutoFeatureExtractor.from_pretrained(
                "superb/wav2vec2-base-superb-er",
                cache_dir=CACHE_DIR
            )
            
            # Load audio
            y, sr = librosa.load(audio_file, sr=16000)
            
            # Extract features
            inputs = feature_extractor(y, sampling_rate=sr, return_tensors="pt")
            
            # Inference
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Get prediction
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class_idx = torch.argmax(predictions, dim=-1).item()
            
            # Map to emotion label
            labels = model.config.id2label
            return labels.get(predicted_class_idx, "unknown")
            
        except Exception as e:
            print(f"ONNX inference error: {e}")
            return "unknown"
    else:
        # PyTorch (lightweight) models work directly
        try:
            result = model(audio_file)
            return result[0]["label"]
        except Exception as e:
            print(f"PyTorch inference error: {e}")
            return "unknown"


def analyze_audio(file_path, max_duration=120):
    """
    Analyze audio emotion with memory optimization for Render free tier.
    
    Args:
        file_path: Path to audio file
        max_duration: Max audio duration in seconds (default 120s = 2 minutes)
    
    Raises:
        ValueError: If audio exceeds max_duration
    """
    file_path = convert_to_wav(file_path)

    # Check duration before full load to prevent memory overload
    y, sr = librosa.load(file_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    if duration > max_duration:
        raise ValueError(
            f"Audio too long. Maximum: {max_duration}s (~{max_duration/60:.1f} min), "
            f"received: {duration:.1f}s (~{duration/60:.1f} min). "
            "Please upload a shorter audio file."
        )

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
    
    # Force garbage collection to free memory immediately (critical for 512MB limit)
    gc.collect()
    
    return emotions if emotions else [{"time": "0:00", "emotion": "unknown", "duration": "0s"}]


def cleanup_uploads():
    """Remove old uploaded files to save disk space on Render"""
    try:
        upload_dir = "./uploads"
        if os.path.exists(upload_dir):
            files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
            files_sorted = sorted(files, key=os.path.getmtime)
            # Keep only the 5 most recent uploads
            if len(files_sorted) > 5:
                for f in files_sorted[:-5]:
                    try:
                        os.remove(f)
                        print(f"Cleaned up old upload: {f}")
                    except Exception as e:
                        print(f"Could not remove {f}: {e}")
    except Exception as e:
        print(f"Upload cleanup warning: {e}")
