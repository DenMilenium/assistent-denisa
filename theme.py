"""
Assistent denisa — Modern UI Theme (Linear-inspired dark design)
"""

from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QGradient
from PyQt6.QtCore import Qt

# === Linear-inspired Color Palette ===
BG_PRIMARY = "#08090A"       # Deepest background
BG_PANEL = "#0F1011"         # Panel/sidebar background
BG_SURFACE = "#191A1B"       # Elevated surface (cards)
BG_SECONDARY = "#28282C"     # Secondary surface (hover)
BG_INPUT = "rgba(255,255,255,0.02)"  # Input background

TEXT_PRIMARY = "#F7F8F8"     # Primary text (near-white)
TEXT_SECONDARY = "#D0D6E0"   # Body/secondary text
TEXT_TERTIARY = "#8A8F98"    # Muted text
TEXT_QUATERNARY = "#62666D"  # Subtle labels

BRAND_INDIGO = "#5E6AD2"     # Primary brand
BRAND_ACCENT = "#7170FF"     # Interactive accent
BRAND_HOVER = "#828FFF"      # Hover state
BRAND_GREEN = "#10B981"      # Success green
BRAND_RED = "#EF4444"        # Error/danger
BRAND_ORANGE = "#F59E0B"     # Warning

BORDER_SUBTLE = "rgba(255,255,255,0.05)"
BORDER_STANDARD = "rgba(255,255,255,0.08)"
BORDER_SOLID = "#23252A"

# === Typography ===
FONT_FAMILY = "Segoe UI, system-ui, -apple-system, sans-serif"
FONT_MONO = "Consolas, JetBrains Mono, ui-monospace, monospace"
FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_MD = 13
FONT_SIZE_LG = 15
FONT_SIZE_XL = 20
FONT_SIZE_HERO = 32

# === Spacing ===
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_2XL = 32
SPACING_3XL = 48

# === Layout ===
BORDER_RADIUS_SM = 4
BORDER_RADIUS_MD = 6
BORDER_RADIUS_LG = 8
BORDER_RADIUS_PILL = 9999

# === Stylesheets ===

STYLE_APP = f"""
QMainWindow, QWidget {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_MD}px;
}}

QTabWidget::pane {{
    background-color: {BG_PRIMARY};
    border: none;
    border-top: 1px solid {BORDER_STANDARD};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {TEXT_TERTIARY};
    padding: 10px 20px;
    margin: 0;
    border: none;
    font-size: {FONT_SIZE_MD}px;
    font-weight: 500;
    min-width: 100px;
}}

QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
    background-color: rgba(255,255,255,0.03);
}}

QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {BRAND_ACCENT};
}}

QGroupBox {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_STANDARD};
    border-radius: {BORDER_RADIUS_LG}px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 500;
    font-size: {FONT_SIZE_SM}px;
    color: {TEXT_SECONDARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_STANDARD};
    border-bottom: none;
    border-radius: {BORDER_RADIUS_MD}px {BORDER_RADIUS_MD}px 0px 0px;
    color: {TEXT_SECONDARY};
}}
"""

STYLE_TABLE = f"""
QTableWidget {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STANDARD};
    border-radius: {BORDER_RADIUS_LG}px;
    gridline-color: {BORDER_SUBTLE};
    selection-background-color: rgba(113, 112, 255, 0.15);
    selection-color: {TEXT_PRIMARY};
    padding: 2px;
    font-size: {FONT_SIZE_MD}px;
}}

QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {BORDER_SUBTLE};
}}

QTableWidget::item:hover {{
    background-color: rgba(255,255,255,0.03);
}}

QHeaderView::section {{
    background-color: {BG_SECONDARY};
    color: {TEXT_TERTIARY};
    padding: 8px 8px;
    border: none;
    border-bottom: 1px solid {BORDER_STANDARD};
    font-weight: 500;
    font-size: {FONT_SIZE_SM}px;
    text-transform: uppercase;
}}
"""

STYLE_PROGRESS_BAR = f"""
QProgressBar {{
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 4px;
    text-align: center;
    height: 24px;
    background-color: rgba(255,255,255,0.03);
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_SM}px;
    font-weight: 500;
}}

/* Color variants set inline */
QProgressBar::chunk {{
    border-radius: 3px;
}}
"""

STYLE_BUTTON_PRIMARY = f"""
QPushButton {{
    background-color: {BRAND_INDIGO};
    color: white;
    border: none;
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 8px 16px;
    font-size: {FONT_SIZE_MD}px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {BRAND_HOVER};
}}

QPushButton:pressed {{
    background-color: {BRAND_INDIGO};
}}
"""

STYLE_BUTTON_GHOST = f"""
QPushButton {{
    background-color: rgba(255,255,255,0.02);
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_STANDARD};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 7px 14px;
    font-size: {FONT_SIZE_MD}px;
    font-weight: 400;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: rgba(255,255,255,0.05);
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255,255,255,0.12);
}}

QPushButton:pressed {{
    background-color: rgba(255,255,255,0.08);
}}
"""

STYLE_BUTTON_DANGER = f"""
QPushButton {{
    background-color: rgba(239, 68, 68, 0.1);
    color: {BRAND_RED};
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 7px 14px;
    font-size: {FONT_SIZE_MD}px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.4);
}}
"""

STYLE_INPUT = f"""
QLineEdit, QTimeEdit {{
    background-color: rgba(255,255,255,0.02);
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STANDARD};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 8px 12px;
    font-size: {FONT_SIZE_MD}px;
    min-height: 20px;
}}

QLineEdit:focus, QTimeEdit:focus {{
    border: 1px solid {BRAND_ACCENT};
    background-color: rgba(255,255,255,0.04);
}}

QLineEdit::placeholder {{
    color: {TEXT_TERTIARY};
}}
"""

STYLE_CHECKBOX = f"""
QCheckBox {{
    spacing: 6px;
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_MD}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid {BORDER_SOLID};
    background-color: transparent;
}}

QCheckBox::indicator:checked {{
    background-color: {BRAND_GREEN};
    border: 1.5px solid {BRAND_GREEN};
}}

QCheckBox::indicator:hover {{
    border: 1.5px solid {TEXT_TERTIARY};
}}
"""

STYLE_TEXT_EDIT = f"""
QTextEdit {{
    background-color: rgba(255,255,255,0.02);
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 8px;
    font-size: {FONT_SIZE_SM}px;
}}
"""

STYLE_LABEL_HEADER = f"""
QLabel {{
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_XL}px;
    font-weight: 600;
    letter-spacing: -0.3px;
}}
"""

STYLE_LABEL_MUTED = f"""
QLabel {{
    color: {TEXT_TERTIARY};
    font-size: {FONT_SIZE_SM}px;
}}
"""

STYLE_SCROLLBAR = f"""
QScrollBar:vertical {{
    background-color: {BG_PRIMARY};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: rgba(255,255,255,0.08);
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: rgba(255,255,255,0.12);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {BG_PRIMARY};
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: rgba(255,255,255,0.08);
    border-radius: 4px;
    min-width: 30px;
}}
"""

STYLE_DIALOG = f"""
QDialog {{
    background-color: {BG_SURFACE};
}}

QDialog QLabel {{
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_MD}px;
}}
"""


def apply_theme(app):
    """Apply all stylesheets to the application."""
    all_styles = (
        STYLE_APP +
        STYLE_TABLE +
        STYLE_PROGRESS_BAR +
        STYLE_INPUT +
        STYLE_CHECKBOX +
        STYLE_TEXT_EDIT +
        STYLE_SCROLLBAR +
        STYLE_DIALOG +
        # Set default button style to ghost
        STYLE_BUTTON_GHOST
    )
    
    app.setStyleSheet(all_styles)
    
    # Set default font
    font = QFont(FONT_FAMILY.split(",")[0].strip(), FONT_SIZE_MD)
    app.setFont(font)
    
    return app


def get_button_style(style_type="ghost"):
    """Get button stylesheet by type."""
    styles = {
        "primary": STYLE_BUTTON_PRIMARY,
        "ghost": STYLE_BUTTON_GHOST,
        "danger": STYLE_BUTTON_DANGER,
    }
    return styles.get(style_type, styles["ghost"])


def style_progress_with_color(color):
    """Progress bar stylesheet with custom color."""
    return f"""
    QProgressBar {{
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 4px;
        text-align: center;
        height: 24px;
        background-color: rgba(255,255,255,0.03);
        color: {TEXT_SECONDARY};
        font-size: {FONT_SIZE_SM}px;
        font-weight: 500;
    }}
    QProgressBar::chunk {{
        background-color: {color};
        border-radius: 3px;
    }}
    """
