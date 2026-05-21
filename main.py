"""Assistent denisa — Entry Point"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme
from gui import MainWindow
from greeting_screen import GreetingManager
from voice_assistant import create_greeting, text_to_speech, play_audio
import database
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


def start_bot_thread():
    """Start Telegram bot in background thread when token is set."""
    token = database.get_setting("telegram_token")
    if not token:
        return
    try:
        import threading as _t
        from telegram_bot import start_bot as _start_bot
        _t.Thread(target=_start_bot, daemon=True).start()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Bot start failed: {e}")


def delayed_greeting(window):
    # Show greeting
    manager = GreetingManager(window)
    overlay = manager.show_greeting()
    
    # Start Telegram bot after greeting
    QTimer.singleShot(2000, start_bot_thread)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Assistent denisa")
    
    # Apply NEON FUTURE theme
    from neon_theme import apply_neon_theme
    apply_neon_theme(app)
    
    from gui import MainWindow
    window = MainWindow()
    window.show()
    
    # Show greeting after 500ms (after window fully renders)
    QTimer.singleShot(500, lambda: delayed_greeting(window))
    
    sys.exit(app.exec())
