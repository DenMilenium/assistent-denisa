"""
Neon Future Theme — футуристический дизайн 2050 года
Неон, глитч-эффекты, голографические элементы, плавные анимации
"""

from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# === NEON FUTURE COLOR PALETTE ===
BG_DEEP_SPACE = "#0A0A0F"          # Космическая чернота
BG_PANEL_DARK = "#0D0D15"          # Панели с лёгким фиолетовым отливом
BG_SURFACE = "#12121E"             # Поверхности
BG_CARD = "#1A1A2E"                # Карточки
BG_CARD_HOVER = "#222244"         
BG_GLOW = "rgba(100, 80, 255, 0.05)"

TEXT_NEON_WHITE = "#E8E8FF"        # Белый с голубым отливом
TEXT_NEON_BLUE = "#7B9CFF"         # Неоново-голубой
TEXT_NEON_PURPLE = "#B47CFF"       # Неоново-фиолетовый  
TEXT_NEON_CYAN = "#00F5FF"         # Неоново-циан
TEXT_NEON_PINK = "#FF6B9D"         # Неоново-розовый
TEXT_NEON_GREEN = "#00FF87"        # Неоново-зелёный
TEXT_NEON_ORANGE = "#FFB347"       # Неоново-оранжевый
TEXT_MUTED = "#6B6B80"            # Приглушённый

BORDER_NEON = "rgba(100, 80, 255, 0.15)"
BORDER_NEON_BRIGHT = "rgba(100, 80, 255, 0.3)"
BORDER_NEON_GLOW = "rgba(0, 245, 255, 0.2)"

# === GLASS EFFECT ===
GLASS_BG = "rgba(18, 18, 30, 0.85)"
GLASS_BORDER = "rgba(255, 255, 255, 0.06)"
GLASS_HIGHLIGHT = "rgba(255, 255, 255, 0.02)"

# === FONTS ===
FONT_FAMILY = "'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Consolas', 'Courier New', monospace"

# === ANIMATION ===
TRANSITION_FAST = "150ms"
TRANSITION_NORMAL = "300ms"
TRANSITION_SLOW = "500ms"

# === MASTER STYLESHEET ===
MASTER_STYLE = f"""
/* GLOBAL */
QMainWindow, QWidget {{
    background-color: {BG_DEEP_SPACE};
    color: {TEXT_NEON_WHITE};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

/* === HEADERS === */
QLabel[id="header"] {{
    color: {TEXT_NEON_WHITE};
    font-size: 28px;
    font-weight: 200;
    letter-spacing: 1px;
}}

QLabel[id="subheader"] {{
    color: {TEXT_MUTED};
    font-size: 14px;
    font-weight: 300;
}}

/* === TABS === */
QTabWidget::pane {{
    background-color: {BG_DEEP_SPACE};
    border: none;
    border-top: 1px solid {BORDER_NEON};
    position: absolute;
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 12px 24px;
    margin: 0;
    border: none;
    font-size: 13px;
    font-weight: 500;
    min-width: 90px;
    letter-spacing: 0.5px;
}}

QTabBar::tab:hover {{
    color: {TEXT_NEON_WHITE};
}}

QTabBar::tab:selected {{
    color: {TEXT_NEON_CYAN};
    border-bottom: 2px solid {TEXT_NEON_CYAN};
}}

/* === GROUP BOXES (Glass Cards) === */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_NEON};
    border-radius: 16px;
    margin-top: 14px;
    padding: 20px 16px 16px 16px;
    font-weight: 500;
    font-size: 12px;
    color: {TEXT_NEON_CYAN};
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 14px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_CARD}, stop:1 {BG_DEEP_SPACE});
    border: 1px solid {BORDER_NEON};
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    color: {TEXT_NEON_CYAN};
    font-weight: 500;
    letter-spacing: 1px;
}}

/* === BUTTONS === */
QPushButton {{
    background-color: {BG_CARD};
    color: {TEXT_NEON_WHITE};
    border: 1px solid {BORDER_NEON};
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {BG_CARD_HOVER};
    border: 1px solid {BORDER_NEON_BRIGHT};
}}

QPushButton:pressed {{
    background-color: #2A2A50;
}}

/* === PRIMARY BUTTON (NEON) === */
QPushButton[id="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5B3AFF, stop:0.5 #7B4CFF, stop:1 #3A7BFF);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

QPushButton[id="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6B4AFF, stop:0.5 #8B5CFF, stop:1 #4A8BFF);
}}

/* === DANGER BUTTON === */
QPushButton[id="danger"] {{
    background: rgba(255, 107, 157, 0.1);
    color: {TEXT_NEON_PINK};
    border: 1px solid rgba(255, 107, 157, 0.3);
}}

QPushButton[id="danger"]:hover {{
    background: rgba(255, 107, 157, 0.2);
}}

/* === SUCCESS BUTTON === */
QPushButton[id="success"] {{
    background: rgba(0, 255, 135, 0.1);
    color: {TEXT_NEON_GREEN};
    border: 1px solid rgba(0, 255, 135, 0.3);
}}

QPushButton[id="success"]:hover {{
    background: rgba(0, 255, 135, 0.2);
}}

/* === TABLE === */
QTableWidget {{
    background-color: {BG_PANEL_DARK};
    color: {TEXT_NEON_WHITE};
    border: 1px solid {BORDER_NEON};
    border-radius: 12px;
    gridline-color: rgba(100, 80, 255, 0.08);
    selection-background-color: rgba(100, 80, 255, 0.2);
    selection-color: {TEXT_NEON_WHITE};
    padding: 4px;
}}

QTableWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid rgba(100, 80, 255, 0.05);
}}

QTableWidget::item:hover {{
    background-color: rgba(100, 80, 255, 0.05);
}}

QHeaderView::section {{
    background-color: {BG_DEEP_SPACE};
    color: {TEXT_NEON_CYAN};
    padding: 10px 10px;
    border: none;
    border-bottom: 1px solid {BORDER_NEON};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* === PROGRESS BARS === */
QProgressBar {{
    border: 1px solid {BORDER_NEON};
    border-radius: 6px;
    text-align: center;
    height: 26px;
    background-color: rgba(100, 80, 255, 0.05);
    color: {TEXT_NEON_WHITE};
    font-size: 12px;
    font-weight: 500;
    font-family: {FONT_MONO};
}}

QProgressBar::chunk {{
    border-radius: 5px;
}}

/* === INPUTS === */
QLineEdit, QTimeEdit, QTextEdit {{
    background-color: {BG_PANEL_DARK};
    color: {TEXT_NEON_WHITE};
    border: 1px solid {BORDER_NEON};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    min-height: 18px;
}}

QLineEdit:focus, QTimeEdit:focus, QTextEdit:focus {{
    border: 1px solid {BORDER_NEON_BRIGHT};
    background-color: {BG_CARD};
}}

QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}

/* === CHECKBOX === */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_NEON_WHITE};
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1.5px solid {BORDER_NEON};
    background-color: transparent;
}}

QCheckBox::indicator:checked {{
    background-color: {TEXT_NEON_GREEN};
    border: 1.5px solid {TEXT_NEON_GREEN};
}}

QCheckBox::indicator:hover {{
    border-color: {TEXT_NEON_CYAN};
}}

/* === SCROLLBARS === */
QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {BORDER_NEON};
    border-radius: 3px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {BORDER_NEON_BRIGHT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* === COMBOBOX === */
QComboBox {{
    background-color: {BG_PANEL_DARK};
    color: {TEXT_NEON_WHITE};
    border: 1px solid {BORDER_NEON};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QComboBox:hover {{
    border: 1px solid {BORDER_NEON_BRIGHT};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

/* === TOOLTIP === */
QToolTip {{
    background-color: {BG_CARD};
    color: {TEXT_NEON_WHITE};
    border: 1px solid {BORDER_NEON_BRIGHT};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}}
"""


def apply_neon_theme(app):
    """Apply the neon future theme to the application."""
    app.setStyleSheet(MASTER_STYLE)
    
    # Default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)
    
    return app


def get_button_style(style_type="default"):
    """Get button stylesheet by type."""
    styles = {
        "primary": f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5B3AFF, stop:0.5 #7B4CFF, stop:1 #3A7BFF);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6B4AFF, stop:0.5 #8B5CFF, stop:1 #4A8BFF);
            }}
        """,
        "ghost": f"""
            QPushButton {{
                background-color: {BG_CARD};
                color: {TEXT_NEON_WHITE};
                border: 1px solid {BORDER_NEON};
                border-radius: 10px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {BG_CARD_HOVER};
                border: 1px solid {BORDER_NEON_BRIGHT};
            }}
        """,
        "danger": f"""
            QPushButton {{
                background: rgba(255, 107, 157, 0.1);
                color: {TEXT_NEON_PINK};
                border: 1px solid rgba(255, 107, 157, 0.3);
                border-radius: 10px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 107, 157, 0.2);
            }}
        """,
        "success": f"""
            QPushButton {{
                background: rgba(0, 255, 135, 0.1);
                color: {TEXT_NEON_GREEN};
                border: 1px solid rgba(0, 255, 135, 0.3);
                border-radius: 10px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: rgba(0, 255, 135, 0.2);
            }}
        """,
        "neon_pulse": f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 255, 0.1), stop:0.5 rgba(180, 124, 255, 0.15), stop:1 rgba(0, 245, 255, 0.1));
                color: {TEXT_NEON_CYAN};
                border: 1px solid {BORDER_NEON_GLOW};
                border-radius: 10px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 245, 255, 0.2), stop:0.5 rgba(180, 124, 255, 0.25), stop:1 rgba(0, 245, 255, 0.2));
            }}
        """,
    }
    return styles.get(style_type, styles["ghost"])
