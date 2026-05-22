"""
STT Engine — Speech-to-Text для голосовых сообщений
Поддерживает Vosk (оффлайн, русский), Whisper и Google Speech Recognition
"""
import io, os, logging, tempfile, json
from pathlib import Path

logger = logging.getLogger(__name__)

# Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Vosk (offline Russian STT)
VOSK_AVAILABLE = False
VOSK_MODEL = None
try:
    from vosk import Model, KaldiRecognizer
    import wave
    base = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(base, "vosk_model", "vosk-model-small-ru-0.22"),
        os.path.join(base, "vosk_model"),
    ]:
        if os.path.isdir(candidate):
            try:
                VOSK_MODEL = Model(candidate)
                VOSK_AVAILABLE = True
                logger.info(f"Vosk loaded: {candidate}")
                break
            except:
                continue
    if not VOSK_AVAILABLE:
        for root, dirs, _ in os.walk(base):
            for d in dirs:
                if "vosk" in d.lower():
                    try:
                        VOSK_MODEL = Model(os.path.join(root, d))
                        VOSK_AVAILABLE = True
                        logger.info(f"Vosk found: {d}")
                        break
                    except:
                        continue
            if VOSK_AVAILABLE:
                break
except Exception as e:
    logger.warning(f"Vosk unavailable: {e}")

# Google Speech Recognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# FFmpeg
FFMPEG_AVAILABLE = False
try:
    import subprocess
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    FFMPEG_AVAILABLE = True
except:
    pass

AUDIO_CACHE = Path(os.path.dirname(os.path.abspath(__file__))) / "audio_cache"
AUDIO_CACHE.mkdir(exist_ok=True)

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if not WHISPER_AVAILABLE:
        return None
    if _whisper_model is None:
        try:
            _whisper_model = whisper.load_model("base")
        except:
            return None
    return _whisper_model


def transcribe_with_vosk(audio_path: str) -> str:
    """Transcribe using Vosk (offline, Russian)."""
    if not VOSK_AVAILABLE or not VOSK_MODEL:
        return None
    try:
        wf = wave.open(audio_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            wf.close()
            return None
        rec = KaldiRecognizer(VOSK_MODEL, wf.getframerate())
        rec.SetWords(True)
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        result = json.loads(rec.FinalResult())
        wf.close()
        text = result.get("text", "").strip()
        return text if text else None
    except Exception as e:
        logger.warning(f"Vosk error: {e}")
        return None


def transcribe_with_google(audio_path: str) -> str:
    if not SR_AVAILABLE:
        return None
    try:
        recognizer = sr.Recognizer()
        wav_path = audio_path
        if audio_path.endswith(".ogg"):
            from stt_engine import convert_ogg_to_wav
            wav_path = convert_ogg_to_wav(audio_path)
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language="ru-RU")
        except:
            try:
                return recognizer.recognize_google(audio, language="en-US")
            except:
                return None
    except Exception as e:
        logger.warning(f"Google STT error: {e}")
        return None


def transcribe_from_file(audio_path: str) -> str:
    """Try Vosk first (offline), then Google, then Whisper."""
    text = transcribe_with_vosk(audio_path)
    if text:
        return text
    if SR_AVAILABLE:
        text = transcribe_with_google(audio_path)
    if text:
        return text
    if WHISPER_AVAILABLE:
        text = transcribe_with_whisper(audio_path)
    return text


def transcribe_with_whisper(audio_path: str) -> str:
    model = get_whisper_model()
    if not model:
        return None
    try:
        if audio_path.endswith(".ogg"):
            audio_path = convert_ogg_to_wav(audio_path)
        result = model.transcribe(audio_path, language="ru", task="transcribe", fp16=False)
        return result.get("text", "").strip()
    except:
        return None


def convert_ogg_to_wav(ogg_path: str) -> str:
    wav_path = ogg_path.replace(".ogg", ".wav")
    if not FFMPEG_AVAILABLE:
        return ogg_path
    try:
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", wav_path],
                       capture_output=True, check=True)
        return wav_path
    except:
        return ogg_path


def save_telegram_voice(voice_bytes: bytes) -> str:
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ogg_path = str(AUDIO_CACHE / f"voice_{timestamp}.ogg")
    with open(ogg_path, "wb") as f:
        f.write(voice_bytes)
    return ogg_path


def transcribe_voice_bytes(voice_bytes: bytes) -> str:
    from datetime import datetime
    ogg_path = save_telegram_voice(voice_bytes)
    text = transcribe_with_vosk(ogg_path)
    if text is None and SR_AVAILABLE:
        text = transcribe_with_google(ogg_path)
    try:
        os.remove(ogg_path)
        wav = ogg_path.replace(".ogg", ".wav")
        if os.path.exists(wav):
            os.remove(wav)
    except:
        pass
    return text


def record_from_mic(duration: int = 5, sample_rate: int = 16000) -> str:
    if not SR_AVAILABLE:
        logger.warning("SpeechRecognition not installed")
        return None
    
    use_sounddevice = False
    try:
        import sounddevice
        use_sounddevice = True
    except ImportError:
        try:
            import pyaudio
        except ImportError:
            logger.warning("No audio input library")
            return None
    
    try:
        import tempfile, wave
        
        if use_sounddevice:
            import sounddevice as sd
            import numpy as np
            logger.info(f"Recording {duration}s...")
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            tmp = tempfile.NamedTemporaryFile(suffix="_mic.wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            return tmp_path
        else:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone(sample_rate=sample_rate) as source:
                logger.info("Recording...")
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=duration, phrase_time_limit=duration)
            tmp = tempfile.NamedTemporaryFile(suffix="_mic.wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            wav_data = audio.get_wav_data()
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(wav_data)
            return tmp_path
    except Exception as e:
        logger.error(f"Mic error: {e}")
        return None


from datetime import datetime
