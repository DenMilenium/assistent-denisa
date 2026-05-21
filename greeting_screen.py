"""
Greeting Screen — показывает фото ассистента + приветствие голосом
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QApplication, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient, QBrush, QPainterPath

from voice_assistant import create_greeting, speak, play_audio, text_to_speech
from theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    BG_PRIMARY, BG_PANEL, BG_SURFACE,
    BRAND_ACCENT, BRAND_INDIGO, BRAND_GREEN,
    BORDER_STANDARD, BORDER_SUBTLE,
)

import threading
import os
import logging

logger = logging.getLogger(__name__)


class GreetingOverlay(QWidget):
    """Full-screen greeting overlay with photo and voice."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(parent.geometry() if parent else QApplication.primaryScreen().geometry())
        
        self.opacity = 0.0
        self.setup_ui()
        self.start_animation()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center card
        card = QFrame()
        card.setFixedSize(420, 580)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_STANDARD};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(12)
        
        # Animated avatar
        from live_avatar import AnimatedAvatarWidget
        self.avatar_widget = AnimatedAvatarWidget()
        self.avatar_widget.setFixedSize(200, 200)
        card_layout.addWidget(self.avatar_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status dot
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {BRAND_GREEN}; font-size: 10px;")
        status_label = QLabel("В сети")
        status_label.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 12px;")
        status_layout.addWidget(status_dot)
        status_layout.addWidget(status_label)
        card_layout.addLayout(status_layout)
        
        # Greeting text
        self.greeting_label = QLabel("Привет, Денис! 👋")
        self.greeting_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700;
            letter-spacing: -0.5px;
        """)
        self.greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.greeting_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Загружаю расписание...")
        self.subtitle_label.setStyleSheet(f"""
            color: {TEXT_TERTIARY}; font-size: 14px;
        """)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setMaximumWidth(350)
        card_layout.addWidget(self.subtitle_label)
        
        # Skip button
        self.skip_btn = QPushButton("Пропустить →")
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255,255,255,0.05);
                color: {TEXT_TERTIARY};
                border: 1px solid {BORDER_STANDARD};
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.08);
                color: {TEXT_PRIMARY};
            }}
        """)
        self.skip_btn.clicked.connect(self.close)
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_layout.addWidget(self.skip_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Sound wave animation dots (bottom of card)
        dots_layout = QHBoxLayout()
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_colors = [TEXT_TERTIARY, TEXT_TERTIARY, TEXT_TERTIARY]
        self.dots = []
        for color in dot_colors:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 6px; opacity: 0.5;")
            dots_layout.addWidget(dot)
            self.dots.append(dot)
        card_layout.addLayout(dots_layout)
    
    def start_animation(self):
        """Fade in and play greeting."""
        # Fade in
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        
        # Speak greeting after fade
        greeting_text = create_greeting()
        
        # Set subtitle
        # Truncate for display
        display_text = greeting_text[:100] + "..." if len(greeting_text) > 100 else greeting_text
        self.subtitle_label.setText(display_text)
        
        # Speak greeting in background thread (GUI-safe via signals)
        def _speak():
            try:
                # Signal avatar to speak
                self.avatar_widget.avatar.set_speaking.emit(True)
                
                file_path = text_to_speech(greeting_text)
                if file_path:
                    import time
                    time.sleep(0.8)
                    play_audio(file_path)
                
                # Signal avatar to stop
                self.avatar_widget.avatar.set_speaking.emit(False)
            except Exception as e:
                logger.warning(f"Greeting speech failed: {e}")
        
        threading.Thread(target=_speak, daemon=True).start()
        
        # Auto-close after greeting
        QTimer.singleShot(7000, self.close)
    
    def closeEvent(self, event):
        """Stop avatar animation when closing."""
        if hasattr(self, 'avatar_widget') and hasattr(self.avatar_widget, 'avatar'):
            self.avatar_widget.avatar.set_speaking(False)
        super().closeEvent(event)
    
    def paintEvent(self, event):
        """Draw dark overlay behind card."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(8, 9, 10, 200))
        painter.end()


class GreetingManager:
    """Manages greeting flow on app startup."""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.greeting_shown = False
    
    def show_greeting(self):
        """Show greeting overlay."""
        if self.greeting_shown:
            return
        
        self.greeting_shown = True
        overlay = GreetingOverlay(self.parent)
        overlay.show()
        
        return overlay
