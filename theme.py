# theme.py
from PyQt6 import QtWidgets

_DARK_QSS = """
* {
    font-size: 14pt;
    color: #e6e6e6;
}
QWidget {
    background: #1f1f1f;
}
QTableCornerButton::section {
    background: #303030;
    border: 0px;
}
QHeaderView::section {
    background: #303030;
    color: #dcdcdc;
    padding: 6px;
    border: 0px;
}

QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
}
QTableWidget {
    gridline-color: #3a3a3a;
    background: #252525;
    alternate-background-color: #2b2b2b;
    selection-background-color: #3d3d3d;
    selection-color: #ffffff;
}
QHeaderView::section {
    background: #303030;
    color: #dcdcdc;
    padding: 6px;
    border: 0px;
}
QPushButton {
    background: #2e2e2e;
    border: 1px solid #3a3a3a;
    padding: 6px 10px;
    border-radius: 10px;
}
QPushButton:hover {
    background: #3a3a3a;
}
QPushButton:pressed {
    background: #444444;
}
QDialog {
    background: #202020;
}
QMessageBox {
    background: #202020;
}
"""

def apply_dark_theme(widget: QtWidgets.QWidget):
    widget.setStyleSheet(_DARK_QSS)

def apply_dialog_theme(dialog: QtWidgets.QDialog):
    dialog.setStyleSheet(_DARK_QSS)
