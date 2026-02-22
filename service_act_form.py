# Форма добавления/редактирования акта выполненных работ (услуги)
from PyQt6 import QtWidgets
import db
from utils import to_float, format_number_for_edit
from theme import apply_dialog_theme


class ServiceActDialog(QtWidgets.QDialog):
    def __init__(self, contract_id: int, parent=None, act_id: int | None = None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.act_id = act_id
        self.setWindowTitle("Редактировать акт" if act_id else "Добавить акт выполненных работ")
        apply_dialog_theme(self)

        self.period_start_edit = QtWidgets.QLineEdit()
        self.period_start_edit.setPlaceholderText("ГГГГ-ММ-ДД")
        self.period_end_edit = QtWidgets.QLineEdit()
        self.period_end_edit.setPlaceholderText("ГГГГ-ММ-ДД")
        self.act_date_edit = QtWidgets.QLineEdit()
        self.act_date_edit.setPlaceholderText("ГГГГ-ММ-ДД")
        self.amount_edit = QtWidgets.QLineEdit()
        self.amount_edit.setPlaceholderText("Сумма")
        self.amount_edit.editingFinished.connect(self._format_amount)
        self.note_edit = QtWidgets.QLineEdit()
        self.note_edit.setPlaceholderText("Примечание")

        form = QtWidgets.QFormLayout()
        form.addRow("Период с:", self.period_start_edit)
        form.addRow("Период по:", self.period_end_edit)
        form.addRow("Дата акта:", self.act_date_edit)
        form.addRow("Сумма:", self.amount_edit)
        form.addRow("Примечание:", self.note_edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)

        if act_id:
            a = db.get_service_act(act_id)
            if a:
                self.period_start_edit.setText(a.get("period_start") or "")
                self.period_end_edit.setText(a.get("period_end") or "")
                self.act_date_edit.setText(a.get("act_date") or "")
                amt = a.get("amount")
                self.amount_edit.setText(format_number_for_edit(amt) if amt is not None else "")
                self.note_edit.setText(a.get("note") or "")

    def _format_amount(self):
        s = (self.amount_edit.text() or "").strip().replace(" ", "").replace(",", ".")
        if not s:
            return
        try:
            v = float(s)
            self.amount_edit.blockSignals(True)
            self.amount_edit.setText(format_number_for_edit(v))
            self.amount_edit.blockSignals(False)
        except ValueError:
            pass

    def on_accept(self):
        period_start = self.period_start_edit.text().strip()
        period_end = self.period_end_edit.text().strip()
        act_date = self.act_date_edit.text().strip()
        if not act_date:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Укажите дату акта.")
            return
        amount = to_float(self.amount_edit.text())
        note = self.note_edit.text().strip()
        if self.act_id:
            db.update_service_act(self.act_id, period_start, period_end or None, act_date, amount, note or None)
        else:
            db.add_service_act(self.contract_id, period_start, period_end or None, act_date, amount, note or None)
        self.accept()
