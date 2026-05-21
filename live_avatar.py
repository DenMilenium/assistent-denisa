"""
Live Avatar — animated photorealistic avatar with expressions
Uses CSS keyframe animations via QLabel + QTimer for fluid motion
"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve, QRectF, QPointF, pyqtSlot
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen,
    QRadialGradient, QFont, QPainterPath, QGradient,
)
import math
import random


class MouthShape:
    """Animated mouth parameters."""
    CLOSED = 0.0
    OPEN = 1.0
    SMILE = 2.0


class EyeState:
    OPEN = 0.0
    CLOSED = 1.0
    HAPPY = 2.0  # squint


class LiveAvatar(QLabel):
    """
    Animated photorealistic avatar with:
    - Smooth head movement (breathing, slight sway)
    - Eye blinking (random interval)
    - Lip sync simulation
    - Subtle facial expressions
    - Hair, skin, facial features
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        
        # Animation state
        self.blink_timer = 0
        self.breath_phase = 0.0
        self.eye_openness = 1.0  # 0=closed, 1=open
        self.mouth_openness = 0.0
        self.head_tilt = 0.0
        self.eyebrow_height = 0.0
        
        # Animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(50)  # 20 FPS
        
        # Blink timer
        self.next_blink = random.randint(30, 80)  # frames until next blink
        self.is_blinking = False
        
        # Render immediately
        self.render_avatar()

    def animate(self):
        """Frame update — 20 FPS animation loop."""
        self.breath_phase += 0.04
        
        # Natural head sway (subtle)
        self.head_tilt = math.sin(self.breath_phase) * 0.008
        
        # Blink logic
        if self.is_blinking:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = False
                self.next_blink = random.randint(30, 80)
        else:
            self.next_blink -= 1
            if self.next_blink <= 0:
                self.is_blinking = True
                self.blink_timer = 4  # 4 frames = 200ms blink
        
        # Smooth eye transition
        if self.is_blinking:
            blink_progress = self.blink_timer / 4.0
            self.eye_openness = 1.0 - blink_progress
        else:
            self.eye_openness += (1.0 - self.eye_openness) * 0.3
        
        self.render_avatar()
    
    @pyqtSlot(bool)
    def set_speaking(self, is_speaking: bool):
        """Trigger mouth animation for speech."""
        if is_speaking:
            # Random mouth movement
            self.mouth_openness = 0.3 + random.random() * 0.5
            self.eyebrow_height = 0.03  # Slight eyebrow raise
        else:
            self.mouth_openness *= 0.85  # Smooth close
            self.eyebrow_height *= 0.9
    
    def render_avatar(self):
        """Paint the avatar with current animation state."""
        pixmap = QPixmap(180, 180)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Save state for head transform
        painter.save()
        cx, cy = 90, 95  # Center of head
        
        # Apply subtle head sway
        painter.translate(cx, cy)
        painter.rotate(math.degrees(self.head_tilt))
        painter.translate(-cx, -cy)
        
        # === NECK ===
        neck_path = QPainterPath()
        neck_path.addRoundedRect(68, 125, 44, 30, 5, 5)
        painter.fillPath(neck_path, QColor(255, 218, 185))  # Skin tone
        
        # === HAIR (modern short haircut) ===
        # Base hair
        hair_gradient = QLinearGradient(50, 30, 130, 80)
        hair_gradient.setColorAt(0.0, QColor(30, 30, 35))  # Dark brown
        hair_gradient.setColorAt(1.0, QColor(50, 50, 55))
        
        # Main hair volume
        hair_path = QPainterPath()
        hair_path.moveTo(35, 75)
        hair_path.cubicTo(30, 50, 40, 25, 60, 20)
        hair_path.cubicTo(80, 15, 100, 15, 120, 20)
        hair_path.cubicTo(140, 25, 150, 50, 145, 75)
        hair_path.cubicTo(148, 60, 138, 35, 120, 28)
        hair_path.cubicTo(100, 22, 80, 22, 60, 28)
        hair_path.cubicTo(42, 35, 32, 60, 35, 75)
        painter.fillPath(hair_path, QBrush(hair_gradient))
        
        # Hair top volume (more texture)
        top_hair = QPainterPath()
        top_hair.moveTo(50, 65)
        top_hair.cubicTo(48, 42, 60, 25, 80, 22)
        top_hair.cubicTo(95, 20, 110, 22, 120, 28)
        top_hair.cubicTo(110, 35, 90, 30, 70, 35)
        top_hair.cubicTo(60, 40, 55, 50, 58, 65)
        painter.fillPath(top_hair, QColor(35, 35, 40))
        
        # Hair side texture
        left_hair = QPainterPath()
        left_hair.moveTo(35, 75)
        left_hair.cubicTo(30, 65, 32, 52, 38, 45)
        left_hair.cubicTo(40, 55, 38, 65, 42, 72)
        painter.fillPath(left_hair, QColor(25, 25, 30))
        
        right_hair = QPainterPath()
        right_hair.moveTo(145, 75)
        right_hair.cubicTo(150, 65, 148, 52, 142, 45)
        right_hair.cubicTo(140, 55, 142, 65, 138, 72)
        painter.fillPath(right_hair, QColor(25, 25, 30))
        
        # === FACE SHAPE ===
        face_path = QPainterPath()
        face_path.moveTo(45, 70)
        face_path.cubicTo(38, 80, 35, 95, 38, 110)
        face_path.cubicTo(42, 125, 50, 130, 55, 133)
        face_path.cubicTo(60, 136, 68, 138, 80, 138)
        face_path.cubicTo(92, 138, 100, 136, 105, 133)
        face_path.cubicTo(110, 130, 118, 125, 122, 110)
        face_path.cubicTo(125, 95, 122, 80, 115, 70)
        face_path.cubicTo(110, 65, 100, 62, 90, 62)
        face_path.cubicTo(80, 62, 70, 65, 65, 68)
        face_path.cubicTo(55, 65, 48, 67, 45, 70)
        
        # Skin fill
        skin_gradient = QLinearGradient(90, 65, 90, 140)
        skin_gradient.setColorAt(0.0, QColor(255, 215, 180))
        skin_gradient.setColorAt(0.5, QColor(255, 210, 178))
        skin_gradient.setColorAt(1.0, QColor(245, 200, 168))
        painter.fillPath(face_path, QBrush(skin_gradient))
        
        # === EYEBROWS ===
        brow_y_offset = -30 + self.eyebrow_height * 15
        
        # Left eyebrow
        painter.setPen(QPen(QColor(40, 35, 30), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        left_brow = QPainterPath()
        left_brow.moveTo(58, 78 + brow_y_offset)
        left_brow.cubicTo(62, 75 + brow_y_offset, 68, 74 + brow_y_offset, 76, 75 + brow_y_offset)
        painter.drawPath(left_brow)
        
        # Right eyebrow
        right_brow = QPainterPath()
        right_brow.moveTo(104, 78 + brow_y_offset)
        right_brow.cubicTo(100, 75 + brow_y_offset, 94, 74 + brow_y_offset, 86, 75 + brow_y_offset)
        painter.drawPath(right_brow)
        
        # === EYES ===
        eye_open = self.eye_openness
        
        # Left eye
        eye_path_left = QPainterPath()
        eye_path_left.moveTo(62, 95)
        eye_path_left.cubicTo(62, 91, 66, 88, 73, 88)
        eye_path_left.cubicTo(80, 88, 82, 91, 82, 95)
        eye_path_left.cubicTo(82, 95 + 6 * (1 - eye_open), 62, 95 + 6 * (1 - eye_open), 62, 95)
        
        # Eye white
        painter.fillPath(eye_path_left, QColor(240, 240, 250))
        painter.setPen(QPen(QColor(80, 75, 70), 1.0))
        painter.drawPath(eye_path_left)
        
        if eye_open > 0.2:
            # Iris
            pupil_cx, pupil_cy = 72, 93
            iris_r = 5
            painter.setBrush(QColor(70, 100, 140))  # Blue-grey eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(pupil_cx, pupil_cy), iris_r, iris_r * eye_open)
            
            # Pupil
            painter.setBrush(QColor(20, 20, 25))
            painter.drawEllipse(QPointF(pupil_cx, pupil_cy), 2.5, 2.5 * eye_open)
            
            # Eye shine
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawEllipse(QPointF(pupil_cx - 2, pupil_cy - 2), 1.5, 1.5 * eye_open)
        
        # Right eye
        eye_path_right = QPainterPath()
        eye_path_right.moveTo(98, 95)
        eye_path_right.cubicTo(98, 91, 100, 88, 107, 88)
        eye_path_right.cubicTo(114, 88, 118, 91, 118, 95)
        eye_path_right.cubicTo(118, 95 + 6 * (1 - eye_open), 98, 95 + 6 * (1 - eye_open), 98, 95)
        
        painter.fillPath(eye_path_right, QColor(240, 240, 250))
        painter.setPen(QPen(QColor(80, 75, 70), 1.0))
        painter.drawPath(eye_path_right)
        
        if eye_open > 0.2:
            pupil_cx2, pupil_cy2 = 108, 93
            painter.setBrush(QColor(70, 100, 140))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(pupil_cx2, pupil_cy2), iris_r, iris_r * eye_open)
            painter.setBrush(QColor(20, 20, 25))
            painter.drawEllipse(QPointF(pupil_cx2, pupil_cy2), 2.5, 2.5 * eye_open)
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawEllipse(QPointF(pupil_cx2 - 2, pupil_cy2 - 2), 1.5, 1.5 * eye_open)
        
        # === NOSE ===
        painter.setPen(QPen(QColor(200, 170, 150), 1.0))
        nose_path = QPainterPath()
        nose_path.moveTo(90, 96)
        nose_path.cubicTo(87, 100, 86, 105, 83, 110)
        nose_path.cubicTo(83, 113, 85, 115, 90, 115)
        nose_path.cubicTo(95, 115, 97, 113, 97, 110)
        nose_path.cubicTo(94, 105, 93, 100, 90, 96)
        painter.drawPath(nose_path)
        
        # Nostrils
        painter.setBrush(QColor(180, 150, 130))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(85, 113), 1.5, 1.0)
        painter.drawEllipse(QPointF(95, 113), 1.5, 1.0)
        
        # === MOUTH ===
        mouth_open = self.mouth_openness
        
        # Lips
        if mouth_open < 0.3:
            # Closed mouth (slight smile)
            mouth_path = QPainterPath()
            mouth_path.moveTo(68, 122)
            mouth_path.cubicTo(73, 118, 78, 116, 82, 116)
            mouth_path.cubicTo(98, 116, 105, 118, 112, 122)
            mouth_path.cubicTo(105, 125, 98, 127, 82, 127)
            mouth_path.cubicTo(78, 127, 73, 125, 68, 122)
            
            painter.fillPath(mouth_path, QColor(180, 100, 90))
            painter.setPen(QPen(QColor(160, 90, 80), 1.0))
            painter.drawPath(mouth_path)
        else:
            # Open mouth (speaking)
            mouth_w = 44 * (0.5 + mouth_open * 0.5)
            mouth_h = 4 + mouth_open * 10
            mx = 90 - mouth_w / 2
            my = 120
            
            mouth_path = QPainterPath()
            mouth_path.moveTo(mx, my)
            mouth_path.cubicTo(
                mx + mouth_w * 0.25, my - 2,
                mx + mouth_w * 0.75, my - 2,
                mx + mouth_w, my
            )
            mouth_path.cubicTo(
                mx + mouth_w * 0.75, my + mouth_h,
                mx + mouth_w * 0.25, my + mouth_h,
                mx, my
            )
            
            painter.fillPath(mouth_path, QColor(40, 20, 20))  # Inside mouth
            painter.setPen(QPen(QColor(180, 100, 90), 1.5))
            painter.drawPath(mouth_path)
        
        # === JAWLINE / CHIN ===
        painter.setPen(QPen(QColor(220, 185, 160), 1.0))
        jaw_path = QPainterPath()
        jaw_path.moveTo(55, 133)
        jaw_path.cubicTo(60, 136, 68, 138, 80, 138)
        jaw_path.cubicTo(92, 138, 100, 136, 105, 133)
        painter.drawPath(jaw_path)
        
        # === EARS ===
        # Left ear
        painter.setBrush(QColor(255, 210, 178))
        painter.setPen(QPen(QColor(230, 185, 155), 1.0))
        painter.drawEllipse(QRectF(38, 85, 12, 18))
        
        # Right ear
        painter.drawEllipse(QRectF(130, 85, 12, 18))
        
        # === Subtle skin highlights ===
        # Nose bridge highlight
        highlight = QRadialGradient(90, 100, 20)
        highlight.setColorAt(0.0, QColor(255, 230, 200, 40))
        highlight.setColorAt(1.0, QColor(255, 230, 200, 0))
        painter.setBrush(QBrush(highlight))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(75, 85, 30, 40))
        
        # === Neck shadow ===
        neck_shadow = QPainterPath()
        neck_shadow.addRect(80, 135, 20, 10)
        neck_shadow_grad = QLinearGradient(90, 135, 90, 145)
        neck_shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 30))
        neck_shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(neck_shadow, QBrush(neck_shadow_grad))
        
        painter.restore()
        painter.end()
        
        self.setPixmap(pixmap)


class AnimatedAvatarWidget(QWidget):
    """
    Widget containing the animated avatar with subtle glow.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtle glow background
        self.glow = QLabel(self)
        self.glow.setFixedSize(180, 180)
        self.glow.setStyleSheet("""
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, 
                stop:0 rgba(94, 106, 210, 30), stop:0.5 rgba(113, 112, 255, 10), stop:1 transparent);
            border-radius: 90px;
        """)
        self.glow.move(10, 10)
        
        # Avatar
        self.avatar = LiveAvatar(self)
        self.avatar.move(10, 10)
        
        layout.addStretch()
    
    def set_speaking(self, is_speaking: bool):
        self.avatar.set_speaking(is_speaking)
