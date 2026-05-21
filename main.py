"""Assistent denisa — Entry Point"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme
from gui import main
from greeting_screen import GreetingManager
from voice_assistant import create_greeting, text_to_speech, play_audio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


def delayed_greeting(window):
    """Show greeting overlay after window is displayed."""
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
