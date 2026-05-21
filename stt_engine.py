"""
STT Engine — Speech-to-Text для голосовых сообщений
Поддерживает Whisper (локально) и Google Speech Recognition
"""

import io
import os
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Try importing SpeechRecognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# FFmpeg for audio conversion
FFMPEG_AVAILABLE = False
try:
    import subprocess
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    FFMPEG_AVAILABLE = True
except:
    pass

AUDIO_CACHE = Path(os.path.dirname(os.path.abspath(__file__))) / "audio_cache"
AUDIO_CACHE.mkdir(exist_ok=True)

# Whisper model (lazy loaded)
_whisper_model = None


def get_whisper_model():
    """Get or load whisper model."""
    global _whisper_model
    if not WHISPER_AVAILABLE:
        return None
    if _whisper_model is None:
        try:
            logger.info("Loading Whisper model 'base' (this may take a moment)...")
            _whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded!")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            return None
    return _whisper_model


def convert_ogg_to_wav(ogg_path: str) -> str:
    """Convert OGG audio to WAV using ffmpeg."""
    wav_path = ogg_path.replace(".ogg", ".wav")
    
    if not FFMPEG_AVAILABLE:
        # Try to use pydub or just copy
        logger.warning("FFmpeg not available, trying direct read")
        return ogg_path
    
    try:
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", ogg_path,
            "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
            wav_path
        ], capture_output=True, check=True)
        return wav_path
    except Exception as e:
        logger.warning(f"FFmpeg conversion failed: {e}")
        return ogg_path


def transcribe_with_whisper(audio_path: str) -> str:
    """Transcribe audio using Whisper (best quality, Russian supported)."""
    model = get_whisper_model()
    if not model:
        return None
    
    try:
        # Convert to wav if needed
        if audio_path.endswith(".ogg"):
            audio_path = convert_ogg_to_wav(audio_path)
        
        result = model.transcribe(
            audio_path,
            language="ru",
            task="transcribe",
            fp16=False,  # CPU mode
        )
        text = result.get("text", "").strip()
        logger.info(f"Whisper: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


def transcribe_with_google(audio_path: str) -> str:
    """Transcribe audio using Google Speech Recognition."""
    if not SR_AVAILABLE:
        logger.warning("SpeechRecognition not installed")
        return None
    
    try:
        recognizer = sr.Recognizer()
        
        # Convert to wav first
        wav_path = audio_path
        if audio_path.endswith(".ogg"):
            wav_path = convert_ogg_to_wav(audio_path)
        
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        
        # Try Russian first, then English
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
        except sr.UnknownValueError:
            try:
                text = recognizer.recognize_google(audio, language="en-US")
            except sr.UnknownValueError:
                return None
        
        logger.info(f"Google STT: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Google STT failed: {e}")
        return None


def save_telegram_voice(voice_bytes: bytes) -> str:
    """Save Telegram voice bytes to temporary file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ogg_path = str(AUDIO_CACHE / f"voice_{timestamp}.ogg")
    
    with open(ogg_path, "wb") as f:
        f.write(voice_bytes)
    
    return ogg_path


def transcribe_voice_bytes(voice_bytes: bytes) -> str:
    """
    Transcribe voice message bytes.
    Tries Whisper first, falls back to Google STT.
    Returns transcribed text or None.
    """
    from datetime import datetime
    
    # Save to temp file
    ogg_path = save_telegram_voice(voice_bytes)
    
    text = None
    
    # Try Whisper (best quality)
    if WHISPER_AVAILABLE:
        text = transcribe_with_whisper(ogg_path)
    
    # Fallback to Google
    if text is None and SR_AVAILABLE:
        text = transcribe_with_google(ogg_path)
    
    # Cleanup temp file
    try:
        os.remove(ogg_path)
        wav_path = ogg_path.replace(".ogg", ".wav")
        if os.path.exists(wav_path):
            os.remove(wav_path)
    except:
        pass
    
    return text


# Import here to avoid circular imports
from datetime import datetime


def record_from_mic(duration: int = 5, sample_rate: int = 16000) -> str:
    """
    Record audio from microphone, save to temporary WAV file.
    Returns path to WAV file or None on failure.
    """
    if not SR_AVAILABLE:
        logger.warning("SpeechRecognition not installed — cannot record from mic")
        return None
    
    # Check if we can record (sounddevice or pyaudio)
    use_sounddevice = False
    try:
        import sounddevice
        use_sounddevice = True
        logger.info("Using sounddevice for microphone capture")
    except ImportError:
        try:
            import pyaudio
        except ImportError:
            logger.warning("Neither PyAudio nor sounddevice installed. Install with: pip install sounddevice")
            return None
    
    try:
        import speech_recognition as sr
        import tempfile
        import wave
        
        r = sr.Recognizer()
        
        if use_sounddevice:
            # Use sounddevice directly (works without PyAudio)
            import sounddevice as sd
            import numpy as np
            
            logger.info(f"Recording {duration}s from microphone (sounddevice)...")
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            # Save to temporary WAV
            tmp = tempfile.NamedTemporaryFile(suffix="_mic.wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            
            logger.info(f"Recording saved: {tmp_path}")
            return tmp_path
        else:
            # Use PyAudio via speech_recognition
            with sr.Microphone(sample_rate=sample_rate) as source:
                logger.info("Recording from microphone...")
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=duration, phrase_time_limit=duration)
            
            # Save to temporary WAV
            tmp = tempfile.NamedTemporaryFile(suffix="_mic.wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            
            wav_data = audio.get_wav_data()
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(wav_data)
            
            logger.info(f"Recording saved: {tmp_path}")
            return tmp_path
    except Exception as e:
        logger.error(f"Microphone recording failed: {e}")
        return None
