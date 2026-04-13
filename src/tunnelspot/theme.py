from __future__ import annotations

from PySide6.QtGui import QColor, QPalette


PALETTE = {
    "bg_top": "#f3efe6",
    "bg_bottom": "#dfeef0",
    "card": "#fcfbf8",
    "card_border": "rgba(16, 34, 38, 0.08)",
    "text_primary": "#102226",
    "text_secondary": "#5b6d71",
    "accent": "#1d8d86",
    "accent_soft": "#d5f1ec",
    "danger": "#c65b4b",
    "danger_soft": "#f8dfd8",
    "field": "#f5f4f0",
    "field_border": "rgba(16, 34, 38, 0.12)",
}


def build_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(PALETTE["bg_top"]))
    palette.setColor(QPalette.WindowText, QColor(PALETTE["text_primary"]))
    palette.setColor(QPalette.Base, QColor(PALETTE["field"]))
    palette.setColor(QPalette.AlternateBase, QColor(PALETTE["card"]))
    palette.setColor(QPalette.Text, QColor(PALETTE["text_primary"]))
    palette.setColor(QPalette.Button, QColor(PALETTE["card"]))
    palette.setColor(QPalette.ButtonText, QColor(PALETTE["text_primary"]))
    palette.setColor(QPalette.Highlight, QColor(PALETTE["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return palette


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        color: {PALETTE["text_primary"]};
        selection-background-color: {PALETTE["accent"]};
        selection-color: white;
    }}

    QMainWindow {{
        background: transparent;
    }}

    QLabel#eyebrow {{
        color: {PALETTE["accent"]};
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    QLabel#title {{
        font-size: 34px;
        font-weight: 700;
    }}

    QLabel#subtitle {{
        color: {PALETTE["text_secondary"]};
        font-size: 14px;
        line-height: 1.45;
    }}

    QFrame#card {{
        background: {PALETTE["card"]};
        border: 1px solid {PALETTE["card_border"]};
        border-radius: 28px;
    }}

    QLabel#sectionTitle {{
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: {PALETTE["text_secondary"]};
        text-transform: uppercase;
    }}

    QLabel#bodyMuted {{
        color: {PALETTE["text_secondary"]};
        font-size: 13px;
    }}

    QLabel#statusChip {{
        background: {PALETTE["accent_soft"]};
        border-radius: 14px;
        color: {PALETTE["accent"]};
        font-weight: 700;
        padding: 6px 12px;
    }}

    QLabel#statusChip[danger="true"] {{
        background: {PALETTE["danger_soft"]};
        color: {PALETTE["danger"]};
    }}

    QLineEdit, QComboBox {{
        background: {PALETTE["field"]};
        border: 1px solid {PALETTE["field_border"]};
        border-radius: 16px;
        padding: 12px 14px;
        min-height: 22px;
        font-size: 14px;
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {PALETTE["accent"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}

    QPushButton {{
        border: none;
        border-radius: 16px;
        padding: 11px 16px;
        font-size: 14px;
        font-weight: 600;
        background: {PALETTE["field"]};
    }}

    QPushButton:hover {{
        background: #ece9e1;
    }}

    QPushButton:pressed {{
        background: #e3dfd7;
    }}

    QPushButton#accentButton {{
        background: {PALETTE["accent"]};
        color: white;
    }}

    QPushButton#accentButton:hover {{
        background: #177972;
    }}

    QPushButton#ghostButton {{
        background: transparent;
        border: 1px solid {PALETTE["field_border"]};
    }}
    """
