"""
Live Avatar — Cyberpunk Neon Animated Avatar
Fluid particle-based avatar with expressions, glow, and speech reactivity
В стиле deep space (#0A0A0F) с violet→cyan градиентами
"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen,
    QRadialGradient, QPainterPath, QFont, QConicalGradient,
)
import math
import random


class Particle:
    """Floating particle around the avatar."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = random.uniform(0.0, 1.0)
        self.y = random.uniform(0.0, 1.0)
        self.vx = random.uniform(-0.003, 0.003)
        self.vy = random.uniform(-0.003, 0.003)
        self.size = random.uniform(1.0, 3.5)
        self.alpha = random.uniform(0.1, 0.6)
        self.phase = random.uniform(0, 2 * math.pi)
        self.color = random.choice([
            QColor(180, 130, 255),   # violet
            QColor(100, 200, 255),   # cyan
            QColor(200, 100, 255),   # magenta
            QColor(120, 220, 255),   # light cyan
        ])
    
    def update(self, time: float):
        self.x += self.vx
        self.y += self.vy
        self.alpha = 0.2 + 0.4 * (0.5 + 0.5 * math.sin(time * 2 + self.phase))
        
        # Bounce off edges
        if self.x < 0 or self.x > 1:
            self.vx *= -1
        if self.y < 0 or self.y > 1:
            self.vy *= -1


class LiveAvatar(QLabel):
    """
    Cyberpunk neon animated avatar with:
    - Fluid particle constellation (head shape)
    - Pulsing neon glow ring
    - Eye animation (blink, look around)
    - Mouth react to speech
    - Floating particles around
    - Color shifts (violet ↔ cyan)
    """
    
    # Signals for thread-safe control
    set_speaking = pyqtSignal(bool)
    set_mood_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        
        # Connect signals to slots
        self.set_speaking.connect(self.on_speaking_changed)
        self.set_mood_signal.connect(self._on_set_mood)
        
        # Animation state
        self.time = 0.0
        self.eye_openness = 1.0
        self.mouth_openness = 0.0
        self.mood = "neutral"  # neutral, happy, thinking, speaking
        self.speech_energy = 0.0  # 0-1 for lip sync
        self.glow_pulse = 0.0
        self.look_x = 0.0
        self.look_y = 0.0
        
        # Particles
        self.particles = [Particle() for _ in range(30)]
        
        # Blink state
        self.next_blink = random.randint(30, 80)
        self.is_blinking = False
        self.blink_timer = 0
        
        # Look direction
        self.look_target_x = 0.0
        self.look_target_y = 0.0
        self.look_timer = 0
        
        # Animation timer (30 FPS — smoother)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(33)
        
        # Render initial frame
        self.render_frame()
    
    def animate(self):
        self.time += 0.05
        
        # --- Blink ---
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
            blink_progress = self.blink_timer / 4.0
            self.eye_openness = 1.0 - blink_progress
        else:
            self.eye_openness += (1.0 - self.eye_openness) * 0.3
        
        # --- Look direction (random gentle saccades) ---
        self.look_timer -= 1
        if self.look_timer <= 0:
            self.look_target_x = random.uniform(-0.3, 0.3)
            self.look_target_y = random.uniform(-0.15, 0.15)
            self.look_timer = random.randint(30, 100)
        self.look_x += (self.look_target_x - self.look_x) * 0.08
        self.look_y += (self.look_target_y - self.look_y) * 0.08
        
        # --- Speech energy decay ---
        if self.mood != "speaking":
            self.mouth_openness *= 0.92
            self.speech_energy *= 0.85
        
        # --- Glow pulse ---
        self.glow_pulse = 0.5 + 0.5 * math.sin(self.time * 0.7)
        
        # --- Update particles ---
        for p in self.particles:
            p.update(self.time)
        
        self.render_frame()
    
    @pyqtSlot(bool)
    def on_speaking_changed(self, is_speaking: bool):
        if is_speaking:
            self.mood = "speaking"
            self.speech_energy = min(1.0, self.speech_energy + 0.3)
            # Random mouth movement for speech
            self.mouth_openness = 0.3 + random.random() * 0.5
        else:
            if self.mood == "speaking":
                self.mood = "neutral"
    
    @pyqtSlot(str)
    def _on_set_mood(self, mood: str):
        """Slot for set_mood_signal — thread-safe mood change."""
        if mood in ("neutral", "happy", "thinking", "speaking"):
            self.mood = mood
    
    def set_mood(self, mood: str):
        """Set avatar mood: neutral, happy, thinking, speaking"""
        if mood in ("neutral", "happy", "thinking", "speaking"):
            self.mood = mood
    
    def render_frame(self):
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        cx, cy = 100, 100  # center
        
        # === 1. OUTER GLOW RING ===
        glow_r = 70 + 5 * self.glow_pulse * (0.8 + 0.2 * self.speech_energy)
        glow_alpha = int(30 + 20 * self.glow_pulse + 30 * self.speech_energy)
        
        glow = QRadialGradient(cx, cy, glow_r)
        glow_color = QColor(140, 90, 255)  # violet
        glow.setColorAt(0.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        glow.setColorAt(0.7, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), glow_alpha))
        glow.setColorAt(1.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)
        
        # === 2. INNER GLOW (cyan) ===
        inner_r = 45 + 3 * self.glow_pulse
        inner_glow = QRadialGradient(cx, cy, inner_r)
        inner_glow.setColorAt(0.0, QColor(100, 200, 255, 15))
        inner_glow.setColorAt(0.8, QColor(80, 180, 255, 5))
        inner_glow.setColorAt(1.0, QColor(80, 180, 255, 0))
        painter.setBrush(QBrush(inner_glow))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)
        
        # === 3. HEAD — fluid neon contours (cyberpunk style) ===
        # Head is drawn as a glowing elliptical silhouette
        head_cx, head_cy = cx, cy - 5
        head_w = 52 + 2 * math.sin(self.time * 0.5)
        head_h = 64 + 2 * math.cos(self.time * 0.3)
        
        # Head fill (semi-transparent neon)
        head_gradient = QRadialGradient(head_cx, head_cy, head_w)
        head_gradient.setColorAt(0.0, QColor(200, 150, 255, 80))
        head_gradient.setColorAt(0.6, QColor(140, 90, 255, 40))
        head_gradient.setColorAt(1.0, QColor(80, 180, 255, 10))
        painter.setBrush(QBrush(head_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(head_cx, head_cy), head_w, head_h)
        
        # Head outline (neon wireframe)
        head_pen = QPen(QColor(180, 130, 255, 120 + 60 * self.glow_pulse), 1.5)
        painter.setPen(head_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(head_cx, head_cy), head_w, head_h)
        
        # === 4. EYES ===
        eye_open = self.eye_openness
        eye_y = head_cy - 8 + self.look_y * 3
        
        # Pupil radius
        pupil_r = 3 * eye_open
        
        # Left eye
        lex, ley = head_cx - 14 + self.look_x * 2, eye_y
        # Eye socket glow
        leye_glow = QRadialGradient(lex, ley, 10)
        leye_glow.setColorAt(0.0, QColor(200, 180, 255, 60))
        leye_glow.setColorAt(1.0, QColor(200, 180, 255, 0))
        painter.setBrush(QBrush(leye_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(lex, ley), 10, 10)
        
        # Eye shape
        if eye_open > 0.1:
            eye_path = QPainterPath()
            eye_path.moveTo(lex - 7, ley)
            eye_path.cubicTo(lex - 7, ley - 5 * eye_open, lex - 2, ley - 6 * eye_open, lex + 2, ley - 6 * eye_open)
            eye_path.cubicTo(lex + 6, ley - 6 * eye_open, lex + 7, ley - 5 * eye_open, lex + 7, ley)
            eye_path.cubicTo(lex + 7, ley + 5 * eye_open, lex + 6, ley + 6 * eye_open, lex + 2, ley + 6 * eye_open)
            eye_path.cubicTo(lex - 2, ley + 6 * eye_open, lex - 7, ley + 5 * eye_open, lex - 7, ley)
            
            # Glowing iris
            iris_color = QColor(100, 200, 255, 200) if self.mood != "thinking" else QColor(200, 150, 255, 200)
            painter.setBrush(QBrush(iris_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(eye_path)
            
            # Pupil
            pupil_r = 3 * eye_open
            painter.setBrush(QColor(30, 30, 50, 220))
            painter.drawEllipse(QPointF(lex + self.look_x, ley + self.look_y), pupil_r, pupil_r * 1.2)
            
            # Eye shine
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawEllipse(QPointF(lex - 2 + self.look_x, ley - 2 + self.look_y), 1.5, 1.5)
        else:
            # Closed eye — single glowing line
            painter.setPen(QPen(QColor(180, 130, 255, 180), 2))
            painter.drawLine(int(lex - 6), int(ley), int(lex + 6), int(ley))
        
        # Right eye
        rex, rey = head_cx + 14 + self.look_x * 2, eye_y
        reye_glow = QRadialGradient(rex, rey, 10)
        reye_glow.setColorAt(0.0, QColor(200, 180, 255, 60))
        reye_glow.setColorAt(1.0, QColor(200, 180, 255, 0))
        painter.setBrush(QBrush(reye_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(rex, rey), 10, 10)
        
        if eye_open > 0.1:
            eye_path2 = QPainterPath()
            eye_path2.moveTo(rex - 7, rey)
            eye_path2.cubicTo(rex - 7, rey - 5 * eye_open, rex - 2, rey - 6 * eye_open, rex + 2, rey - 6 * eye_open)
            eye_path2.cubicTo(rex + 6, rey - 6 * eye_open, rex + 7, rey - 5 * eye_open, rex + 7, rey)
            eye_path2.cubicTo(rex + 7, rey + 5 * eye_open, rex + 6, rey + 6 * eye_open, rex + 2, rey + 6 * eye_open)
            eye_path2.cubicTo(rex - 2, rey + 6 * eye_open, rex - 7, rey + 5 * eye_open, rex - 7, rey)
            
            iris_color2 = QColor(100, 200, 255, 200) if self.mood != "thinking" else QColor(200, 150, 255, 200)
            painter.setBrush(QBrush(iris_color2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(eye_path2)
            
            painter.setBrush(QColor(30, 30, 50, 220))
            painter.drawEllipse(QPointF(rex + self.look_x, rey + self.look_y), pupil_r, pupil_r * 1.2)
            
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawEllipse(QPointF(rex - 2 + self.look_x, rey - 2 + self.look_y), 1.5, 1.5)
        else:
            painter.setPen(QPen(QColor(180, 130, 255, 180), 2))
            painter.drawLine(int(rex - 6), int(rey), int(rex + 6), int(rey))
        
        # === 5. MOUTH ===
        mouth_y = head_cy + 18
        mouth_open = self.mouth_openness
        
        if mouth_open < 0.15:
            # Closed — subtle smile line (neon)
            smile_path = QPainterPath()
            smile_path.moveTo(head_cx - 12, mouth_y)
            smile_path.cubicTo(head_cx - 6, mouth_y + 3 * (0.5 + 0.5 if self.mood == "happy" else 0.3),
                              head_cx + 6, mouth_y + 3 * (0.5 + 0.5 if self.mood == "happy" else 0.3),
                              head_cx + 12, mouth_y)
            painter.setPen(QPen(QColor(255, 150, 200, 180), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(smile_path)
        else:
            # Open mouth — neon glowing mouth
            mw = 20 + mouth_open * 10
            mh = 4 + mouth_open * 12
            
            mouth_gradient = QLinearGradient(head_cx - mw/2, mouth_y, head_cx + mw/2, mouth_y + mh)
            mouth_gradient.setColorAt(0.0, QColor(255, 100, 150, 200))
            mouth_gradient.setColorAt(0.5, QColor(255, 60, 120, 200))
            mouth_gradient.setColorAt(1.0, QColor(200, 80, 150, 200))
            
            mouth_path = QPainterPath()
            mouth_path.moveTo(head_cx - mw/2, mouth_y)
            mouth_path.cubicTo(head_cx - mw/4, mouth_y - 2, head_cx + mw/4, mouth_y - 2, head_cx + mw/2, mouth_y)
            mouth_path.cubicTo(head_cx + mw/4, mouth_y + mh, head_cx - mw/4, mouth_y + mh, head_cx - mw/2, mouth_y)
            
            painter.fillPath(mouth_path, QBrush(mouth_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(mouth_path)
        
        # === 6. GLOWING DOTS (like cyberpunk facial decoration) ===
        dot_alpha = int(100 + 50 * self.glow_pulse)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Forehead dot
        painter.setBrush(QColor(180, 130, 255, dot_alpha))
        painter.drawEllipse(QPointF(head_cx, head_cy - 32), 2.5, 2.5)
        
        # Cheek dots
        painter.setBrush(QColor(100, 200, 255, dot_alpha))
        painter.drawEllipse(QPointF(head_cx - 30, head_cy + 6), 2, 2)
        painter.drawEllipse(QPointF(head_cx + 30, head_cy + 6), 2, 2)
        
        # === 7. SPEECH WAVES (when speaking) ===
        if self.speech_energy > 0.1:
            wave_alpha = int(40 * self.speech_energy)
            painter.setPen(QPen(QColor(100, 200, 255, wave_alpha), 1))
            for i in range(5):
                x_offset = (i - 2) * 18
                wave_y = head_cy + 35
                wave_h = 5 + 10 * self.speech_energy * (0.5 + 0.5 * math.sin(self.time * 4 + i))
                wave_path = QPainterPath()
                wave_path.moveTo(head_cx + x_offset - 5, wave_y)
                wave_path.cubicTo(
                    head_cx + x_offset - 5, wave_y + wave_h,
                    head_cx + x_offset + 5, wave_y + wave_h,
                    head_cx + x_offset + 5, wave_y,
                )
                painter.drawPath(wave_path)
        
        # === 8. PARTICLES ===
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
    """Container widget with the neon animated avatar."""
    
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
