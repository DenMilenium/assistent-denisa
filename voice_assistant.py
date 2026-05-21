"""
Voice Assistant Module — Assistent denisa
Provides TTS (Edge), audio playback, greeting screen, and voice messages
Uses winsound (built-in) + threaded Edge TTS generation
"""

import os
import io
import asyncio
import threading
import tempfile
import logging
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import TTS engines
try:
    import edge_tts
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False

# Audio playback methods (tried in order)
PLAY_METHOD = None

def _init_player():
    global PLAY_METHOD
    
    # Method 1: winsound (built-in Windows, plays WAV)
    try:
        import winsound
        # Verify winsound actually works with a silent test
        winsound.PlaySound(None, winsound.SND_PURGE)
        PLAY_METHOD = "winsound"
        logger.info("Audio: using winsound (built-in) + PowerShell conversion")
        return
    except Exception:
        pass
    
    # Method 2: PowerShell media playback (always works on Windows 10+)
    import subprocess as _sp
    for ps_cmd in ["powershell.exe", "powershell"]:
        try:
            r = _sp.run(
                [ps_cmd, "-NoProfile", "-Command",
                 "try { $null = New-Object System.Media.SoundPlayer; Write-Output 'ok' } catch { Write-Error $_ }"],
                capture_output=True, timeout=3, text=True
            )
            if r.returncode == 0 and 'ok' in r.stdout:
                PLAY_METHOD = "powershell"
                logger.info(f"Audio: using PowerShell SoundPlayer (via {ps_cmd})")
                return
        except Exception:
            continue
    
    # Method 3: os.startfile (always available on Windows)
    try:
        import platform
        if platform.system() == "Windows":
            import os
            # Just verify we can reach shell
            _sp.run(["cmd", "/c", "ver"], capture_output=True, timeout=2, check=True)
            PLAY_METHOD = "os_default"
            logger.info("Audio: using os.startfile (system default)")
            return
    except Exception:
        pass
    
    PLAY_METHOD = None
    logger.warning("Audio: no playback method available")


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

    if filename is None:
        safe_name = "".join(c for c in text if c.isalnum() or c in " _-")[:30]
        filename = f"tts_{safe_name}.mp3"
    
    output_path = AUDIO_CACHE / filename
    
    if output_path.exists():
        return str(output_path)

    try:
        async def _tts():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
        
        asyncio.run(_tts())
        logger.info(f"TTS saved: {output_path}")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return None


def play_audio_impl(file_path: str):
    """Play audio using available method."""
    global PLAY_METHOD
    
    if PLAY_METHOD is None:
        _init_player()
    
    if PLAY_METHOD == "winsound":
        import winsound
        # winsound only plays WAV, so we try to play directly
        try:
            winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            # Fallback: try to convert on the fly
            convert_and_play(file_path)
    
    elif PLAY_METHOD == "playsound":
        try:
            from playsound import playsound
            playsound(file_path, block=False)
        except:
            convert_and_play(file_path)
    
    elif PLAY_METHOD == "powershell":
        play_with_powershell(file_path)
    
    elif PLAY_METHOD == "ffplay":
        play_with_ffplay(file_path)
    
    else:
        # Last resort: try system default
        play_with_os_default(file_path)


def convert_and_play(mp3_path: str):
    """Convert MP3 to WAV and play with winsound."""
    try:
        # Use PowerShell to convert and play
        ps_command = f"""
        Add-Type -AssemblyName System.Windows.Forms;
        $player = New-Object System.Media.SoundPlayer;
        $player.Stream = (New-Object System.IO.MemoryStream(
            ,[System.IO.File]::ReadAllBytes('{mp3_path}')
        ));
        $player.Play();
        """
        threading.Thread(
            target=lambda: subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_command],
                capture_output=True, timeout=30
            ),
            daemon=True
        ).start()
    except Exception as e:
        logger.warning(f"Convert and play failed: {e}")


def play_with_powershell(mp3_path: str):
    """Play audio using PowerShell Media Player (plays any format)."""
    try:
        # PowerShell script that uses Media Player to play MP3
        ps_script = f'''
$path = "{mp3_path}"
$player = New-Object -ComObject MediaPlayer.MediaPlayer
$player.Open($path)
$player.Play()
# Wait for playback
Start-Sleep -Milliseconds 200
while ($player.Status -eq 3) {{ Start-Sleep -Milliseconds 100 }}
'''
        threading.Thread(
            target=lambda: subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, timeout=60
            ),
            daemon=True
        ).start()
    except Exception as e:
        logger.warning(f"PowerShell media play failed: {e}")
        # Final fallback
        play_with_os_default(mp3_path)


def play_with_ffplay(mp3_path: str):
    """Play audio using ffplay."""
    try:
        subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", mp3_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.warning(f"FFplay failed: {e}")


def play_with_os_default(mp3_path: str):
    """Play using OS default player."""
    try:
        import platform
        system = platform.system()
        if system == "Windows":
            os.startfile(mp3_path)
        elif system == "Darwin":
            subprocess.Popen(["afplay", mp3_path])
        else:
            subprocess.Popen(["xdg-open", mp3_path])
    except Exception as e:
        logger.warning(f"OS default play failed: {e}")


def play_audio(file_path: str):
    """Play audio file in background thread."""
    if not os.path.exists(file_path):
        logger.warning(f"Audio file not found: {file_path}")
        return
    
    thread = threading.Thread(target=lambda: play_audio_impl(file_path), daemon=True)
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
    
    hour = now.hour
    if hour < 6:
        time_greet = "Доброй ночи"
    elif hour < 12:
        time_greet = "Доброе утро"
    elif hour < 18:
        time_greet = "Добрый день"
    else:
        time_greet = "Добрый вечер"
    
    try:
        from goals import get_today_schedule, get_urgent_tasks
        from database import get_all_items
        
        today_schedule = get_today_schedule()
        urgent = get_urgent_tasks()
        all_items = get_all_items()
        today_tasks = [i for i in all_items if i["enabled"]]
        
        greeting = f"{time_greet}, Денис! Сегодня {date_str}. "
        
        if urgent:
            top = urgent[0]["name"]
            greeting += f"У тебя срочная задача: {top}. "
        
        if today_schedule:
            priority = today_schedule.get("priority", "")
            if priority:
                greeting += f"Сегодня приоритет: {priority}. "
        
    except Exception as e:
        logger.warning(f"Greeting detail failed: {e}")
        greeting = f"{time_greet}, Денис! Сегодня {date_str}. Я твой личный ассистент."
    
    return greeting


def create_reminder_message(task_text: str, time_str: str) -> str:
    """Create a natural voice reminder message."""
    lower = task_text.lower()
    
    if "обед" in lower or "поесть" in lower or lower.startswith("🍽"):
        return f"Денис, время обедать. Не забудь поесть!"
    if "спорт" in lower or "ходьб" in lower or "бег" in lower or "тренировк" in lower:
        return f"Денис, пора заниматься спортом. {task_text}"
    if "подъём" in lower or "зарядк" in lower:
        return f"Денис, доброе утро! Пора вставать и делать зарядку!"
    if "ужин" in lower:
        return f"Денис, время ужина. Приятного аппетита!"
    if "сон" in lower:
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
    """Create audio bytes suitable for Telegram voice message."""
    return text_to_speech_sync(text, voice)
