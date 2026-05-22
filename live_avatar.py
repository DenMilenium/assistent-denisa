"""
Live Avatar — Photo-based animated avatar with neon effects
Использует фото Дениса как основу + анимация глаз/губ + cyberpunk свечение
"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen,
    QRadialGradient, QPainterPath, QFont,
)
import math
import random
import os


class Particle:
    """Floating neon particle."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = random.uniform(0.0, 1.0)
        self.y = random.uniform(0.0, 1.0)
        self.vx = random.uniform(-0.002, 0.002)
        self.vy = random.uniform(-0.002, 0.002)
        self.size = random.uniform(1.0, 3.0)
        self.alpha = random.uniform(0.1, 0.5)
        self.phase = random.uniform(0, 2 * math.pi)
        self.color = random.choice([
            QColor(180, 130, 255),
            QColor(100, 200, 255),
            QColor(200, 100, 255),
        ])
    
    def update(self, time: float):
        self.x += self.vx
        self.y += self.vy
        self.alpha = 0.15 + 0.35 * (0.5 + 0.5 * math.sin(time * 2 + self.phase))
        if self.x < 0 or self.x > 1: self.vx *= -1
        if self.y < 0 or self.y > 1: self.vy *= -1


class LiveAvatar(QLabel):
    """
    Анимированный аватар на основе фото Дениса.
    - Фото как основа
    - Моргающие глаза с neon свечением
    - Анимированные губы при речи
    - Пульсирующее violet/cyan свечение
    - Плавающие частицы
    """
    
    set_speaking = pyqtSignal(bool)
    set_mood_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        
        # Load photo
        photo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assistent_photo.jpg")
        self.photo = QPixmap(photo_path)
        if self.photo.isNull():
            self.photo = None
        
        # Signals
        self.set_speaking.connect(self.on_speaking_changed)
        self.set_mood_signal.connect(self._on_set_mood)
        
        # Animation state
        self.time = 0.0
        self.eye_openness = 1.0
        self.mouth_openness = 0.0
        self.mood = "neutral"
        self.speech_energy = 0.0
        self.glow_pulse = 0.0
        
        # Particles
        self.particles = [Particle() for _ in range(20)]
        
        # Blink
        self.next_blink = random.randint(60, 150)
        self.is_blinking = False
        self.blink_timer = 0
        
        # Timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(33)
        
        self.render_frame()
    
    def animate(self):
        self.time += 0.05
        
        # Blink
        if self.is_blinking:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = False
                self.next_blink = random.randint(60, 150)
        else:
            self.next_blink -= 1
            if self.next_blink <= 0:
                self.is_blinking = True
                self.blink_timer = 4
        
        if self.is_blinking:
            self.eye_openness = self.blink_timer / 4.0
        else:
            self.eye_openness += (1.0 - self.eye_openness) * 0.3
        
        # Speech
        if self.mood != "speaking":
            self.mouth_openness *= 0.92
            self.speech_energy *= 0.85
        
        # Glow
        self.glow_pulse = 0.5 + 0.5 * math.sin(self.time * 0.7)
        
        for p in self.particles:
            p.update(self.time)
        
        self.render_frame()
    
    @pyqtSlot(bool)
    def on_speaking_changed(self, is_speaking: bool):
        if is_speaking:
            self.mood = "speaking"
            self.speech_energy = min(1.0, self.speech_energy + 0.3)
            self.mouth_openness = 0.3 + random.random() * 0.5
        else:
            if self.mood == "speaking":
                self.mood = "neutral"
    
    @pyqtSlot(str)
    def _on_set_mood(self, mood: str):
        if mood in ("neutral", "happy", "thinking", "speaking"):
            self.mood = mood
    
    def set_mood(self, mood: str):
        if mood in ("neutral", "happy", "thinking", "speaking"):
            self.mood = mood
    
    def render_frame(self):
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        cx, cy = 100, 100
        
        # === 1. Outer glow ring (color by mood) ===
        glow_r = 72 + 4 * self.glow_pulse * (0.8 + 0.2 * self.speech_energy)
        glow_alpha = int(30 + 25 * self.glow_pulse + 25 * self.speech_energy)
        glow = QRadialGradient(cx, cy, glow_r)
        if self.mood == "happy":
            violet = QColor(255, 100, 200)  # pink
        elif self.mood == "thinking":
            violet = QColor(80, 180, 255)   # blue
        elif self.mood == "speaking":
            violet = QColor(180, 100, 255)  # violet-cyan
        else:
            violet = QColor(140, 90, 255)   # default violet
        glow.setColorAt(0.0, QColor(violet.red(), violet.green(), violet.blue(), 0))
        glow.setColorAt(0.7, QColor(violet.red(), violet.green(), violet.blue(), glow_alpha))
        glow.setColorAt(1.0, QColor(violet.red(), violet.green(), violet.blue(), 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)
        
        # === 2. Photo base ===
        if self.photo and not self.photo.isNull():
            # Scale photo to fill 140x140 circle
            scaled = self.photo.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                        Qt.TransformationMode.SmoothTransformation)
            # Create circular clip
            clip_path = QPainterPath()
            clip_path.addEllipse(QRectF(30, 30, 140, 140))
            painter.setClipPath(clip_path)
            # Draw photo centered
            offset_x = (200 - scaled.width()) // 2
            offset_y = (200 - scaled.height()) // 2
            painter.drawPixmap(offset_x, offset_y, scaled)
            painter.setClipping(False)
            
            # === 3. Neon eye overlays ===
            e_open = self.eye_openness
            # Left eye — neon slit
            lex, ley = 82, 88
            if self.mood == "happy":
                eye_color = QColor(255, 180, 220)  # pink eyes
            elif self.mood == "thinking":
                eye_color = QColor(100, 200, 255)  # cyan eyes
            else:
                eye_color = QColor(180, 130, 255)  # violet eyes
            painter.setPen(QPen(eye_color, int(2 * e_open), Qt.PenStyle.SolidLine))
            painter.drawLine(int(lex - 8), int(ley), int(lex + 8), int(ley))
            # Eye glow
            if e_open > 0.3:
                eye_glow = QRadialGradient(lex, ley, 12)
                eye_glow.setColorAt(0.0, QColor(eye_color.red(), eye_color.green(), eye_color.blue(), int(40 * e_open)))
                eye_glow.setColorAt(1.0, QColor(100, 200, 255, 0))
                painter.setBrush(QBrush(eye_glow))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(lex, ley), 12, 12)
            
            # Right eye
            rex, rey = 118, 88
            painter.setPen(QPen(eye_color, int(2 * e_open)))
            painter.drawLine(int(rex - 8), int(rey), int(rex + 8), int(rey))
            if e_open > 0.3:
                eye_glow2 = QRadialGradient(rex, rey, 12)
                eye_glow2.setColorAt(0.0, QColor(eye_color.red(), eye_color.green(), eye_color.blue(), int(40 * e_open)))
                eye_glow2.setColorAt(1.0, QColor(100, 200, 255, 0))
                painter.setBrush(QBrush(eye_glow2))
                painter.drawEllipse(QPointF(rex, rey), 12, 12)
            
            # === 3b. Eyebrow animation by mood ===
            brow_y = 72
            brow_color = QColor(180, 130, 255, 150)
            if self.mood == "happy":
                brow_y = 68  # raised brows
                brow_color = QColor(255, 150, 200, 180)
            elif self.mood == "thinking":
                brow_y = 76  # furrowed
                brow_color = QColor(100, 200, 255, 180)
            elif self.mood == "speaking":
                brow_y = 72
            painter.setPen(QPen(brow_color, 2))
            painter.drawLine(70, brow_y, 90, brow_y - 2)
            painter.drawLine(110, brow_y, 130, brow_y - 2)
            
            # === 4. Mouth animation with emotion ===
            m_open = self.mouth_openness
            mx, my = 100, 118
            
            if self.mood == "happy" and m_open < 0.15:
                # Big happy smile
                painter.setPen(QPen(QColor(255, 100, 150, 200), 2.5))
                smile = QPainterPath()
                smile.moveTo(mx - 14, my)
                smile.cubicTo(mx - 7, my + 7, mx + 7, my + 7, mx + 14, my)
                painter.drawPath(smile)
                # Cheek blush
                blush = QRadialGradient(mx - 25, my - 5, 12)
                blush.setColorAt(0.0, QColor(255, 100, 150, 40))
                blush.setColorAt(1.0, QColor(255, 100, 150, 0))
                painter.setBrush(QBrush(blush))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(mx - 25, my - 5), 12, 8)
                blush2 = QRadialGradient(mx + 25, my - 5, 12)
                blush2.setColorAt(0.0, QColor(255, 100, 150, 40))
                blush2.setColorAt(1.0, QColor(255, 100, 150, 0))
                painter.setBrush(QBrush(blush2))
                painter.drawEllipse(QPointF(mx + 25, my - 5), 12, 8)
            elif self.mood == "thinking":
                # Pursed lips
                painter.setPen(QPen(QColor(200, 150, 200, 150), 2))
                painter.drawLine(mx - 8, my, mx + 8, my)
            elif m_open > 0.15:
                # Speaking
                mw = 14 + m_open * 8
                mh = 3 + m_open * 8
                painter.setBrush(QColor(255, 80, 130, 200))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(mx - mw/2, my - mh/2, mw, mh))
            else:
                # Neutral smile
                painter.setPen(QPen(QColor(255, 100, 150, 120), 1.5))
                smile = QPainterPath()
                smile.moveTo(mx - 10, my)
                smile.cubicTo(mx - 5, my + 3, mx + 5, my + 3, mx + 10, my)
                painter.drawPath(smile)
            
            # === 5. Neon face decorations ===
            dot_alpha = int(80 + 50 * self.glow_pulse)
            painter.setPen(Qt.PenStyle.NoPen)
            # Forehead
            painter.setBrush(QColor(180, 130, 255, dot_alpha))
            painter.drawEllipse(QPointF(100, 55), 2, 2)
            # Cheeks
            painter.setBrush(QColor(100, 200, 255, dot_alpha))
            painter.drawEllipse(QPointF(68, 100), 1.5, 1.5)
            painter.drawEllipse(QPointF(132, 100), 1.5, 1.5)
        else:
            # Fallback if no photo: draw a cyberpunk face
            painter.setPen(QPen(QColor(180, 130, 255, 150), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy - 5), 52, 64)
            # Eyes
            painter.setPen(QPen(QColor(100, 200, 255, 200), 2))
            painter.drawLine(78, 88, 92, 88)
            painter.drawLine(108, 88, 122, 88)
            # Mouth
            painter.setPen(QPen(QColor(255, 80, 130, 150), 1.5))
            painter.drawLine(90, 118, 110, 118)
        
        # === 6. Particles ===
        for p in self.particles:
            px = p.x * 200
            py = p.y * 200
            p_alpha = int(p.alpha * 200)
            p_color = QColor(p.color.red(), p.color.green(), p.color.blue(), p_alpha)
            painter.setBrush(p_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(px, py), p.size, p.size)
        
        painter.end()
        self.setPixmap(pixmap)


class AnimatedAvatarWidget(QWidget):
    """Container with photo-based animated avatar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.avatar = LiveAvatar(self)
        self.avatar.move(10, 10)
        layout.addWidget(self.avatar)
    
    @pyqtSlot(bool)
    def set_speaking(self, is_speaking: bool):
        self.avatar.set_speaking.emit(is_speaking)
    
    def set_mood(self, mood: str):
        self.avatar.set_mood(mood)
