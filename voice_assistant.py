"""
Voice Assistant Module — Assistent denisa
Provides TTS (Edge), audio playback, greeting screen, and voice messages
"""

import os
import io
import asyncio
import threading
import tempfile
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import TTS engines
try:
    import edge_tts
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Voice settings
VOICE_RU_MALE = "ru-RU-DmitryNeural"
VOICE_RU_FEMALE = "ru-RU-SvetlanaNeural"
DEFAULT_VOICE = VOICE_RU_MALE

# Audio cache directory
AUDIO_CACHE = Path(os.path.dirname(os.path.abspath(__file__))) / "audio_cache"
AUDIO_CACHE.mkdir(exist_ok=True)


def get_available_voices() -> list:
    """Get list of available Russian Edge TTS voices."""
    if not EDGE_AVAILABLE:
        return []
    try:
        voices = asyncio.run(edge_tts.list_voices())
        ru_voices = [
            v for v in voices 
            if v["Locale"].startswith("ru") or v["FriendlyName"].startswith("Microsoft Dmitry")
        ]
        return [
            {"name": v["ShortName"], "friendly": v.get("FriendlyName", v["ShortName"])}
            for v in ru_voices[:10]
        ]
    except Exception as e:
        logger.warning(f"Failed to list voices: {e}")
        return []


def text_to_speech(text: str, voice: str = DEFAULT_VOICE, filename: str = None) -> str:
    """
    Convert text to speech using Edge TTS.
    Returns path to audio file.
    """
    if not EDGE_AVAILABLE:
        logger.warning("Edge TTS not installed. Install with: pip install edge-tts")
        return None

    # Sanitize filename
    if filename is None:
        safe_name = text.replace(" ", "_")[:30]
        filename = f"tts_{safe_name}.mp3"
    
    output_path = AUDIO_CACHE / filename
    
    # Check cache
    if output_path.exists():
        return str(output_path)

    try:
        # Run async TTS in sync wrapper
        async def _tts():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
        
        asyncio.run(_tts())
        logger.info(f"TTS saved: {output_path}")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return None


def play_audio(file_path: str):
    """Play audio file in background thread."""
    if not PYGAME_AVAILABLE:
        logger.warning("Pygame not installed. Install with: pip install pygame")
        return
    
    def _play():
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                threading.Event().wait(0.1)
        except Exception as e:
            logger.warning(f"Audio playback failed: {e}")
    
    thread = threading.Thread(target=_play, daemon=True)
    thread.start()


def speak(text: str, voice: str = DEFAULT_VOICE, play_now: bool = True) -> str:
    """Synthesize speech and optionally play it immediately."""
    file_path = text_to_speech(text, voice)
    if file_path and play_now:
        play_audio(file_path)
    return file_path


def create_greeting():
    """Generate greeting text based on current state."""
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    
    # Time of day greeting
    hour = now.hour
    if hour < 6:
        time_greet = "Доброй ночи"
    elif hour < 12:
        time_greet = "Доброе утро"
    elif hour < 18:
        time_greet = "Добрый день"
    else:
        time_greet = "Добрый вечер"
    
    # Get today's schedule info
    try:
        from goals import get_today_schedule, get_urgent_tasks
        from database import get_all_items
        
        today_schedule = get_today_schedule()
        urgent = get_urgent_tasks()
        
        # Count today's tasks
        all_items = get_all_items()
        today_tasks = [i for i in all_items if i["enabled"]]
        
        greeting = (
            f"{time_greet}, Денис! Сегодня {date_str}. "
        )
        
        if urgent:
            top = urgent[0]["name"]
            greeting += f"У тебя срочная задача: {top}. "
        
        if today_schedule:
            priority = today_schedule.get("priority", "")
            if priority:
                greeting += f"Сегодня приоритет: {priority}. "
        
        greeting += "Я твой личный ассистент. Буду напоминать о задачах и помогать держать фокус."
        
    except Exception as e:
        logger.warning(f"Greeting detail failed: {e}")
        greeting = f"{time_greet}, Денис! Сегодня {date_str}. Я твой личный ассистент."
    
    return greeting


def create_reminder_message(task_text: str, time_str: str) -> str:
    """Create a natural voice reminder message."""
    hour = datetime.now().hour
    
    if "обед" in task_text.lower() or "поесть" in task_text.lower() or task_text.lower().startswith("🍽"):
        return f"Денис, время обедать. Не забудь поесть!"
    
    if "спорт" in task_text.lower() or "ходьб" in task_text.lower() or "бег" in task_text.lower() or "тренировк" in task_text.lower():
        return f"Денис, пора заниматься спортом. {task_text}"
    
    if "подъём" in task_text.lower() or "зарядк" in task_text.lower():
        return f"Денис, доброе утро! Пора вставать и делать зарядку!"
    
    if "ужин" in task_text.lower():
        return f"Денис, время ужина. Приятного аппетита!"
    
    if "сон" in task_text.lower():
        return f"Денис, пора готовиться ко сну. Отдохни."
    
    return f"Денис, сейчас {time_str}. Напоминаю: {task_text}"


def text_to_speech_sync(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """Convert text to speech and return raw audio bytes."""
    if not EDGE_AVAILABLE:
        return None
    
    try:
        async def _tts():
            communicate = edge_tts.Communicate(text, voice)
            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            return audio_bytes
        
        return asyncio.run(_tts())
    
    except Exception as e:
        logger.error(f"TTS stream failed: {e}")
        return None


def create_voice_message_bytes(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """Create audio bytes suitable for Telegram voice message (OPUS)."""
    # Edge TTS outputs MP3, Telegram accepts OGG/OPUS
    # We'll convert or just send the raw bytes
    return text_to_speech_sync(text, voice)
