# about_dialog.py
from PyQt6 import QtWidgets
from theme import apply_dialog_theme
from PyQt6.QtCore import Qt

from version import APP_VERSION

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        apply_dialog_theme(self)

        text = (
            "Invest Manager — учёт инвестпроектов\n"
            f"Версия: {APP_VERSION}\n"
            "Автор: Ященко Алексей\n"
            "Назначение: локальный учёт статей, маркетинга, договоров, корректировок и ревизий.\n"
            "ТОО ДП Орталык, рудник Жалпак, 2025 год"
        )
        lbl = QtWidgets.QLabel(text)
        lbl.setWordWrap(True)

        btn = QtWidgets.QPushButton("OK")
        btn.clicked.connect(self.accept)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(lbl)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
