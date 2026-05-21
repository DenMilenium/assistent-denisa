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
    import threading
    from telegram_bot import start_bot
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()


def delayed_greeting(window):
    """Show greeting overlay and start bot."""
    # Start Telegram bot
    token = database.get_setting("telegram_token")
    if token:
        start_bot_thread()
    
    # Show greeting
    manager = GreetingManager(window)
    manager.show_greeting()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Assistent denisa")
    
    # Apply dark theme
    from theme import apply_theme
    apply_theme(app)
    
    from gui import MainWindow
    window = MainWindow()
    window.show()
    
    # Show greeting after 500ms (after window fully renders)
    QTimer.singleShot(500, lambda: delayed_greeting(window))
    
    sys.exit(app.exec())
