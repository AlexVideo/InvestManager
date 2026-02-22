# correction_form.py
from PyQt6 import QtWidgets
from PyQt6.QtCore import QDate
import db
from utils import to_float
from theme import apply_dialog_theme

class CorrectionDialog(QtWidgets.QDialog):
    def __init__(self, project_id: int, parent=None, record_id: int | None = None):
        super().__init__(parent)
        self.project_id = project_id
        self.record_id = record_id
        self.setWindowTitle("Корректировка бюджета" + (" — редактирование" if record_id else ""))
        apply_dialog_theme(self)

        self.new_budget_edit = QtWidgets.QLineEdit()
        self.date_edit = QtWidgets.QDateEdit(); self.date_edit.setCalendarPopup(True); self.date_edit.setDate(QDate.currentDate())
        self.note_edit = QtWidgets.QPlainTextEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Новый бюджет:", self.new_budget_edit)
        form.addRow("Дата:", self.date_edit)
        form.addRow("Примечание:", self.note_edit)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                          QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.on_accept); btns.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self); layout.addLayout(form); layout.addWidget(btns)

        if self.record_id: self._load()

    def _load(self):
        r = db.get_correction(self.record_id)
        if not r: return
        self.new_budget_edit.setText(str(r["new_budget"]))
        y,m,d = map(int, r["date"].split("-")); self.date_edit.setDate(QDate(y,m,d))
        self.note_edit.setPlainText(r["note"] or "")

    def on_accept(self):
        new_budget = to_float(self.new_budget_edit.text())
        date = self.date_edit.date().toString("yyyy-MM-dd")
        note = self.note_edit.toPlainText().strip()
        if self.record_id:
            db.update_correction(self.record_id, new_budget, date, note)
        else:
            db.record_correction(self.project_id, new_budget, date, note)
        self.accept()
