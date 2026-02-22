# bulk_import.py
from PyQt6 import QtWidgets
from theme import apply_dialog_theme
import db
import pyperclip  # pip install pyperclip
import openpyxl
from utils import to_float

class BulkImportDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Массовый импорт проектов")
        self.resize(600, 400)
        apply_dialog_theme(self)

        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setPlaceholderText("Вставьте сюда скопированные из Excel данные (Название | Сумма)...")

        self.load_btn = QtWidgets.QPushButton("Загрузить из файла Excel (.xlsx)")
        self.load_btn.clicked.connect(self.load_from_file)

        self.preview = QtWidgets.QTableWidget(0, 2)
        self.preview.setHorizontalHeaderLabels(["Название", "Бюджет"])
        self.preview.horizontalHeader().setStretchLastSection(True)

        self.ok_btn = QtWidgets.QPushButton("Импортировать")
        self.cancel_btn = QtWidgets.QPushButton("Отмена")

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Вставьте данные (2 колонки: Название, Сумма):"))
        layout.addWidget(self.text_edit)
        layout.addWidget(self.load_btn)
        layout.addWidget(QtWidgets.QLabel("Предпросмотр:"))
        layout.addWidget(self.preview)
        layout.addLayout(btns)

        self.ok_btn.clicked.connect(self.on_import)
        self.cancel_btn.clicked.connect(self.reject)
        self.text_edit.textChanged.connect(self.update_preview)

    def load_from_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Открыть Excel", filter="Excel Files (*.xlsx)")
        if not path:
            return
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        rows = []
        for r in ws.iter_rows(values_only=True):
            if not r or not r[0]:
                continue
            name = str(r[0]).strip()
            budget = to_float(str(r[1])) if len(r) > 1 else 0.0
            rows.append((name, budget))
        self.fill_preview(rows)

    def update_preview(self):
        text = self.text_edit.toPlainText().strip()
        rows = []
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")  # Excel копирует через табуляцию
            name = parts[0].strip()
            budget = to_float(parts[1]) if len(parts) > 1 else 0.0
            rows.append((name, budget))
        self.fill_preview(rows)

    def fill_preview(self, rows):
        self.preview.setRowCount(len(rows))
        for r, (name, budget) in enumerate(rows):
            self.preview.setItem(r, 0, QtWidgets.QTableWidgetItem(name))
            self.preview.setItem(r, 1, QtWidgets.QTableWidgetItem(str(budget)))
        self._rows = rows

    def on_import(self):
        if not hasattr(self, "_rows") or not self._rows:
            QtWidgets.QMessageBox.warning(self, "Импорт", "Нет данных для импорта")
            return
        for name, budget in self._rows:
            if name:
                db.create_project(name, budget, "")
        QtWidgets.QMessageBox.information(self, "Импорт", f"Импортировано {len(self._rows)} проектов")
        self.accept()
