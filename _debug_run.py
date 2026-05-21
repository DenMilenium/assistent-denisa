"""Run the app with crash logging"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Log everything to a file
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_crash.log")
sys.stderr = open(log_file, 'w', encoding='utf-8')

try:
    print("=== Starting Assistent Denisa ===", file=sys.stderr)
    
    import theme
    from gui import MainWindow
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    
    app = QApplication(sys.argv)
    app.setApplicationName("Assistent denisa")
    
    from neon_theme import apply_neon_theme
    apply_neon_theme(app)
    
    from voice_assistant import _init_player
    _init_player()
    print(f"Audio method: {__import__('voice_assistant').PLAY_METHOD}", file=sys.stderr)
    
    window = MainWindow()
    window.show()
    print("Window shown", file=sys.stderr)
    
    # Show greeting after 500ms
    from greeting_screen import GreetingManager
    def delayed():
        try:
            manager = GreetingManager(window)
            overlay = manager.show_greeting()
            print("Greeting shown", file=sys.stderr)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
    
    QTimer.singleShot(500, delayed)
    
    sys.exit(app.exec())
except Exception as e:
    traceback.print_exc(file=sys.stderr)
    print(f"\nFATAL: {e}", file=sys.stderr)
