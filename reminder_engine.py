"""
Daily Schedule Reminder — Reminder Engine
Background thread that checks schedule and fires notifications
"""

import time
import logging
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

import database
import telegram_notifier

logger = logging.getLogger(__name__)

DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
DAY_BITS = [1 << i for i in range(7)]  # Mon=1, Tue=2, ..., Sun=64


def current_day_mask() -> int:
    """Get bitmask for current day (Monday=0, Sunday=6)."""
    today = datetime.now().weekday()  # Monday=0, Sunday=6
    return 1 << today


class ReminderEngine(QThread):
    """Background thread that checks schedule every 30 seconds."""

    notification_signal = pyqtSignal(str, str)  # title, message

    def __init__(self):
        super().__init__()
        self._running = True
        self._fired_minutes: set[str] = set()  # "HH:MM-id" to prevent repeats

    def stop(self):
        self._running = False

    def run(self):
        logger.info("Reminder engine started")
        while self._running:
            try:
                self._check_schedule()
            except Exception as e:
                logger.error(f"Reminder engine error: {e}")
            time.sleep(30)

    def _check_schedule(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today_mask = current_day_mask()

        items = database.get_all_items()

        for item in items:
            if not item["enabled"]:
                continue

            # Check if item should fire today
            if not (item["days_mask"] & today_mask):
                continue

            # Check if time matches
            if item["time"] != current_time:
                continue

            # Check if already fired this minute
            fire_key = f"{current_time}-{item['id']}"
            if fire_key in self._fired_minutes:
                continue

            # Fire!
            self._fired_minutes.add(fire_key)
            self._fire_reminder(item["text"], current_time)

        # Clean old fired minutes (keep only last 10)
        if len(self._fired_minutes) > 100:
            self._fired_minutes.clear()

    def _fire_reminder(self, text: str, time_str: str):
        """Fire a reminder notification."""
        title = f"⏰ {time_str}"
        message = f"🔔 {text}"

        # Emit PC notification signal
        self.notification_signal.emit(title, message)

        # Voice notification on PC
        try:
            from voice_assistant import create_reminder_message, speak
            voice_text = create_reminder_message(text, time_str)
            voice_setting = database.get_setting("notify_voice")
            if voice_setting == "1":
                import threading
                threading.Thread(target=lambda: speak(voice_text), daemon=True).start()
        except Exception as e:
            logger.warning(f"Voice reminder failed: {e}")

        # Send Telegram
        token = database.get_setting("telegram_token")
        chat_id = database.get_setting("telegram_chat_id")
        notify_tg = database.get_setting("notify_telegram") == "1"
        voice_tg = database.get_setting("voice_telegram") == "1"

        if token and chat_id and notify_tg:
            if voice_tg:
                try:
                    from voice_assistant import create_voice_message_bytes, create_reminder_message
                    voice_text_tg = create_reminder_message(text, time_str)
                    audio_data = create_voice_message_bytes(voice_text_tg)
                    if audio_data:
                        telegram_notifier.send_voice(audio_data, token, chat_id)
                    else:
                        tg_text = f"⏰ *{time_str}*\n\n{text}"
                        telegram_notifier.send_telegram(tg_text, token, chat_id)
                except Exception as e:
                    logger.warning(f"Voice TG failed: {e}")
                    tg_text = f"⏰ *{time_str}*\n\n{text}"
                    telegram_notifier.send_telegram(tg_text, token, chat_id)
            else:
                tg_text = f"⏰ *{time_str}*\n\n{text}"
                telegram_notifier.send_telegram(tg_text, token, chat_id)
