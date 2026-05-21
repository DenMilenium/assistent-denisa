"""
Pomodoro Focus Timer — таймер продуктивности с голосовым сопровождением
"""

import time
import logging
import threading
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class FocusMode:
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    STOPPED = "stopped"


class FocusTimer(QThread):
    """Background focus timer thread with voice notifications."""
    
    tick_signal = pyqtSignal(int, str)  # seconds_remaining, state
    complete_signal = pyqtSignal(str)   # state completed
    state_signal = pyqtSignal(str)      # FOCUS / BREAK
    
    TIMES = {
        FocusMode.FOCUS: 25 * 60,      # 25 min
        FocusMode.SHORT_BREAK: 5 * 60,  # 5 min
        FocusMode.LONG_BREAK: 15 * 60,  # 15 min
    }
    
    def __init__(self):
        super().__init__()
        self._running = False
        self._paused = False
        self.current_mode = FocusMode.STOPPED
        self.seconds_left = 0
        self.today_sessions = 0
        self.total_focus_minutes = 0
        self.sessions_completed = 0
    
    def start_focus(self):
        """Start or restart a focus session."""
        if not self._running:
            self._running = True
            self._paused = False
            self.current_mode = FocusMode.FOCUS
            self.seconds_left = self.TIMES[FocusMode.FOCUS]
            self.start()
        else:
            # Reset current
            self._paused = False
            self.current_mode = FocusMode.FOCUS
            self.seconds_left = self.TIMES[FocusMode.FOCUS]
    
    def stop(self):
        self._running = False
        self._paused = False
        self.current_mode = FocusMode.STOPPED
    
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False
    
    def run(self):
        while self._running:
            if not self._paused and self.current_mode != FocusMode.STOPPED:
                try:
                    self.tick_signal.emit(self.seconds_left, self.current_mode)
                    
                    if self.seconds_left <= 0:
                        self._on_session_complete()
                    else:
                        time.sleep(1)
                        self.seconds_left -= 1
                except Exception as e:
                    logger.error(f"Focus timer error: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.1)
    
    def _on_session_complete(self):
        """Handle session completion."""
        if self.current_mode == FocusMode.FOCUS:
            self.sessions_completed += 1
            self.total_focus_minutes += self.TIMES[FocusMode.FOCUS] // 60
            self.today_sessions += 1
            
            # Decide break type
            if self.sessions_completed % 4 == 0:
                self.current_mode = FocusMode.LONG_BREAK
                self.seconds_left = self.TIMES[FocusMode.LONG_BREAK]
            else:
                self.current_mode = FocusMode.SHORT_BREAK
                self.seconds_left = self.TIMES[FocusMode.SHORT_BREAK]
            
            self.complete_signal.emit(FocusMode.FOCUS)
            self.state_signal.emit(self.current_mode)
            
        elif self.current_mode in (FocusMode.SHORT_BREAK, FocusMode.LONG_BREAK):
            self.current_mode = FocusMode.FOCUS
            self.seconds_left = self.TIMES[FocusMode.FOCUS]
            self.complete_signal.emit("break")
            self.state_signal.emit(self.current_mode)
    
    def get_stats(self) -> dict:
        return {
            "today_sessions": self.today_sessions,
            "total_minutes": self.total_focus_minutes,
            "sessions_completed": self.sessions_completed,
        }
