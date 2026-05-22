"""
Hermes Chat — голосовой AI-ассистент на PyQt6
Стиль DeepSeek + голосовой ввод + TTS ответ
"""
import sys, os, threading, time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# === Цвета ===
LIGHT = {
    "bg": "#F5F5F8", "surface": "#FFFFFF", "text": "#1A1A2E",
    "text_sec": "#6B7280", "border": "#E5E7EB",
    "accent": "#4F46E5", "accent2": "#7C3AED",
    "assistant_bg": "#FFFFFF",
}
DARK = {
    "bg": "#0D0D14", "surface": "rgba(255,255,255,0.04)", "text": "#E4E4EC",
    "text_sec": "#9CA3AF", "border": "rgba(255,255,255,0.08)",
    "accent": "#6366F1", "accent2": "#8B5CF6",
    "assistant_bg": "rgba(255,255,255,0.04)",
}


class MessageBubble(QFrame):
    def __init__(self, text, role, colors):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 6, 24, 6)
        
        if role == "user":
            label = QLabel("Вы")
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            label = QLabel("Hermes")
        
        label.setStyleSheet(f"font-size:11px;color:{colors['text_sec']};font-weight:500;letter-spacing:1px;")
        
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size:14px;line-height:1.6;color:{colors['text']};padding:4px 0;")
        msg.setMaximumWidth(600)
        
        if role == "assistant":
            self.setStyleSheet(f"background:{colors['assistant_bg']};border-radius:12px;margin:2px 24px;")
        
        layout.addWidget(label)
        layout.addWidget(msg)


class HermesChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hermes Agent")
        self.setMinimumSize(480, 600)
        self.resize(560, 720)
        
        self.is_dark = False
        self.colors = LIGHT
        self._listening = False
        
        self.init_ui()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === Header ===
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background:{self.colors['bg']};border-bottom:1px solid {self.colors['border']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Hermes")
        title.setStyleSheet(f"font-size:17px;font-weight:700;color:{self.colors['accent']};letter-spacing:-0.3px;")
        hl.addWidget(title)
        hl.addStretch()
        
        self.theme_btn = QPushButton(chr(127769) if not self.is_dark else chr(127774))
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setStyleSheet(f"QPushButton{{background:transparent;border:1px solid {self.colors['border']};border-radius:8px;font-size:14px;}}QPushButton:hover{{background:rgba(79,70,229,0.08);}}")
        self.theme_btn.clicked.connect(self.toggle_theme)
        hl.addWidget(self.theme_btn)
        layout.addWidget(header)
        
        # === Chat ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea{{border:none;background:{self.colors['bg']};}}QScrollBar:vertical{{width:4px;background:transparent;}}QScrollBar::handle:vertical{{background:{self.colors['border']};border-radius:2px;}}")
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(4)
        self.chat_layout.setContentsMargins(0, 16, 0, 16)
        
        # Welcome
        w = QWidget()
        wl = QVBoxLayout(w)
        wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        wi = QLabel(chr(129504))
        wi.setStyleSheet("font-size:48px;")
        wi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(wi)
        
        wt = QLabel("Чем могу помочь?")
        wt.setStyleSheet(f"font-size:26px;font-weight:700;color:{self.colors['text']};letter-spacing:-0.5px;")
        wt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(wt)
        
        ws = QLabel("Спрашивай что угодно — я помогу с кодом, планированием, поиском")
        ws.setStyleSheet(f"font-size:14px;color:{self.colors['text_sec']};")
        ws.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ws.setWordWrap(True)
        ws.setMaximumWidth(400)
        wl.addWidget(ws)
        
        self.welcome = w
        self.chat_layout.addWidget(self.welcome)
        self.chat_layout.addStretch()
        
        scroll.setWidget(self.chat_widget)
        layout.addWidget(scroll, stretch=1)
        
        # === Input ===
        input_area = QWidget()
        input_area.setStyleSheet(f"background:{self.colors['bg']};border-top:1px solid {self.colors['border']};")
        il = QVBoxLayout(input_area)
        il.setContentsMargins(20, 12, 20, 20)
        
        iw = QWidget()
        iw.setStyleSheet(f"background:{self.colors['surface'] if not self.is_dark else 'rgba(255,255,255,0.04)'};border:1px solid {self.colors['border']};border-radius:16px;")
        iwl = QHBoxLayout(iw)
        iwl.setContentsMargins(16, 4, 4, 4)
        
        self.mic_btn = QPushButton(chr(127908))
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;border-radius:8px;font-size:18px;color:{self.colors['text_sec']};}}QPushButton:hover{{color:{self.colors['accent']};background:rgba(79,70,229,0.06);}}")
        self.mic_btn.clicked.connect(self.toggle_mic)
        iwl.addWidget(self.mic_btn)
        
        self.input = QTextEdit()
        self.input.setPlaceholderText("Задай вопрос...")
        self.input.setFixedHeight(40)
        self.input.setMaximumHeight(120)
        self.input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input.setStyleSheet(f"QTextEdit{{background:transparent;border:none;font-size:14px;color:{self.colors['text']};font-family:'Segoe UI',sans-serif;}}QTextEdit::placeholder{{color:{self.colors['text_sec']};}}")
        iwl.addWidget(self.input, stretch=1)
        
        self.send_btn = QPushButton(chr(8594))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {self.colors['accent']},stop:1 {self.colors['accent2']});border:none;border-radius:10px;font-size:18px;color:white;}}QPushButton:hover{{opacity:0.9;}}")
        self.send_btn.clicked.connect(self.send_message)
        iwl.addWidget(self.send_btn)
        
        il.addWidget(iw)
        
        footer = QLabel("Hermes Agent · DeepSeek")
        footer.setStyleSheet(f"font-size:11px;color:{self.colors['text_sec']};padding:6px 0 0 0;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(footer)
        layout.addWidget(input_area)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        self.centralWidget().setStyleSheet(f"background:{self.colors['bg']};")
    
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.colors = DARK if self.is_dark else LIGHT
        self.theme_btn.setText(chr(127774) if self.is_dark else chr(127769))
        self.apply_theme()
    
    # === VOICE ===
    def toggle_mic(self):
        if self._listening:
            self._listening = False
            self.mic_btn.setText(chr(127908))
            self.input.setPlaceholderText("Задай вопрос...")
            return
        
        self._listening = True
        self.mic_btn.setText(chr(11035))
        self.input.setPlaceholderText(chr(127897) + " Слушаю...")
        self.mic_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()
    
    def _listen(self):
        try:
            from stt_engine import record_from_mic
            audio_path = record_from_mic(duration=5)
        except:
            audio_path = None
        
        if not audio_path:
            self._safe_mic_reset(chr(10060) + " Микрофон не доступен")
            return
        
        try:
            from stt_engine import transcribe_from_file, VOSK_AVAILABLE
            text = transcribe_from_file(audio_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            if text:
                self._safe_set_input(text)
                QTimer.singleShot(200, self.send_message)
                return
            else:
                self._safe_mic_reset(chr(129318) + " Не расслышал. Попробуй ещё раз или напиши текст.")
        except Exception as e:
            self._safe_mic_reset(chr(10060) + " Ошибка: " + str(e)[:30])
    
    def _safe_mic_reset(self, msg=None):
        QTimer.singleShot(0, lambda: self.input.setPlaceholderText(msg or "Задай вопрос..."))
        QTimer.singleShot(0, lambda: self.mic_btn.setEnabled(True))
        QTimer.singleShot(0, lambda: self.mic_btn.setText(chr(127908)))
        QTimer.singleShot(0, lambda: setattr(self, '_listening', False))
    
    def _safe_set_input(self, text):
        QTimer.singleShot(0, lambda: self.input.setPlainText(text))
    
    def speak(self, text):
        try:
            from voice_assistant import text_to_speech, play_audio, _init_player
            _init_player()
            path = text_to_speech(text)
            if path and os.path.exists(path):
                play_audio(path)
        except Exception as e:
            pass
    
    # === MESSAGES ===
    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        
        if self.welcome.isVisible():
            self.welcome.hide()
        
        # Add user msg
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, MessageBubble(text, "user", self.colors))
        
        # Typing
        self.typing = QLabel(chr(9679) + " " + chr(9679) + " " + chr(9679))
        self.typing.setStyleSheet(f"font-size:14px;color:{self.colors['accent']};padding:12px 24px;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.typing)
        
        # Process
        QTimer.singleShot(100, lambda: self._process(text))
    
    def _process(self, text):
        t = text.lower()
        response = "Не понял. Расскажи подробнее."
        
        if "привет" in t: response = "Привет, Денис! Я Hermes. Чем могу помочь?"
        elif "занят" in t or "делаешь" in t: response = "Сейчас помогаю с проектом Assistent Denisa! Проверяю код, отвечаю на вопросы, слежу за ассистентом."
        elif "проект" in t: response = "Проект в отличном состоянии!\n\n- Голосовой ассистент с твоим фото\n- VLC для голоса\n- Непрерывный диалог\n- Neon аватар с эмоциями\n- 54/54 тестов\n\nЧего хочешь добиться дальше?"
        elif "кто ты" in t: response = "Я Hermes Agent — AI-помощник на DeepSeek. Помогаю с кодом, планированием, поиском."
        elif "пока" in t or "до свидания" in t: response = "До связи, Денис! Пиши если что 🚀"
        elif "код" in t or "баг" in t: response = "Покажи код или опиши проблему — найду баги и предложу исправления."
        elif "спасиб" in t: response = "Всегда пожалуйста! 😊"
        
        if self.typing:
            self.typing.deleteLater()
            self.typing = None
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, MessageBubble(response, "assistant", self.colors))
        
        # Speak
        thread = threading.Thread(target=lambda: self.speak(response), daemon=True)
        thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Hermes Agent")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = HermesChat()
    window.show()
    sys.exit(app.exec())
