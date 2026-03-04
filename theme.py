# theme.py
from PyQt6 import QtWidgets

# Текущие параметры темы (задаются при старте из app_settings и при смене в настройках)
_font_size_pt = 14
_button_padding = "6px 10px"
_tooltip_font_size_pt = 12


def set_theme_params(
    font_size_pt: int | None = None,
    button_padding: str | None = None,
    tooltip_font_size_pt: int | None = None,
) -> None:
    """Задать параметры темы (шрифт, отступы кнопок, подсказки). None — не менять."""
    global _font_size_pt, _button_padding, _tooltip_font_size_pt
    if font_size_pt is not None:
        _font_size_pt = max(9, min(20, int(font_size_pt)))
    if button_padding is not None:
        _button_padding = button_padding
    if tooltip_font_size_pt is not None:
        _tooltip_font_size_pt = max(9, min(16, int(tooltip_font_size_pt)))


def get_dark_qss() -> str:
    """Собрать QSS тёмной темы из текущих параметров."""
    return f"""
* {{
    font-size: {_font_size_pt}pt;
    color: #e6e6e6;
}}
QWidget {{
    background: #1f1f1f;
}}
QTableCornerButton::section {{
    background: #303030;
    border: 0px;
}}
QHeaderView::section {{
    background: #303030;
    color: #dcdcdc;
    padding: 6px;
    border: 0px;
}}

QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {{
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
}}
QTableWidget {{
    gridline-color: #3a3a3a;
    background: #252525;
    alternate-background-color: #2b2b2b;
    selection-background-color: #3d3d3d;
    selection-color: #ffffff;
}}
QHeaderView::section {{
    background: #303030;
    color: #dcdcdc;
    padding: 6px;
    border: 0px;
}}
QPushButton {{
    background: #2e2e2e;
    border: 1px solid #3a3a3a;
    padding: {_button_padding};
    border-radius: 10px;
}}
QPushButton:hover {{
    background: #3a3a3a;
}}
QPushButton:pressed {{
    background: #444444;
}}
QDialog {{
    background: #202020;
}}
QMessageBox {{
    background: #202020;
}}
QToolTip {{
    background-color: #2a2a2a;
    color: #e6e6e6;
    border: 1px solid #505050;
    padding: 6px;
    font-size: {_tooltip_font_size_pt}pt;
}}
"""


def apply_dark_theme(widget: QtWidgets.QWidget) -> None:
    """Применить тёмную тему к виджету (используются текущие параметры)."""
    widget.setStyleSheet(get_dark_qss())


def apply_dialog_theme(dialog: QtWidgets.QDialog) -> None:
    """Применить тёмную тему к диалогу."""
    dialog.setStyleSheet(get_dark_qss())
