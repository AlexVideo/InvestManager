# Форма добавления/редактирования договора (услуги и работы)
from PyQt6 import QtWidgets
import db
from utils import to_float, format_number_for_edit
from theme import apply_dialog_theme


class ServiceContractDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, contract_id: int | None = None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.setWindowTitle("Редактировать договор" if contract_id else "Добавить договор")
        apply_dialog_theme(self)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Название договора")
        self.contractor_edit = QtWidgets.QLineEdit()
        self.contractor_edit.setPlaceholderText("Контрагент")
        self.total_edit = QtWidgets.QLineEdit()
        self.total_edit.setPlaceholderText("Сумма договора")
        self.total_edit.editingFinished.connect(self._format_total)
        self.start_date_edit = QtWidgets.QLineEdit()
        self.start_date_edit.setPlaceholderText("ГГГГ-ММ-ДД")
        self.end_date_edit = QtWidgets.QLineEdit()
        self.end_date_edit.setPlaceholderText("ГГГГ-ММ-ДД")
        self.mine_combo = QtWidgets.QComboBox()
        self.mine_combo.addItem("—", None)
        for mid, mname in db.list_mines():
            self.mine_combo.addItem(mname, mid)
        self.mine_combo.currentIndexChanged.connect(self._on_mine_changed)
        self.section_combo = QtWidgets.QComboBox()
        self.section_combo.addItem("—", None)
        self.note_edit = QtWidgets.QPlainTextEdit()
        self.note_edit.setMaximumHeight(80)

        form = QtWidgets.QFormLayout()
        form.addRow("Название:", self.name_edit)
        form.addRow("Контрагент:", self.contractor_edit)
        form.addRow("Сумма договора:", self.total_edit)
        form.addRow("Дата начала:", self.start_date_edit)
        form.addRow("Дата окончания:", self.end_date_edit)
        form.addRow("Рудник:", self.mine_combo)
        form.addRow("Участок:", self.section_combo)
        form.addRow("Примечание:", self.note_edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)

        if contract_id:
            c = db.get_service_contract(contract_id)
            if c:
                self.name_edit.setText(c["name"] or "")
                self.contractor_edit.setText(c["contractor"] or "")
                self.total_edit.setText(format_number_for_edit(c["total_amount"]) if c["total_amount"] else "")
                self.start_date_edit.setText(c["start_date"] or "")
                self.end_date_edit.setText(c["end_date"] or "")
                self.note_edit.setPlainText(c["note"] or "")
                mid = c.get("mine_id")
                sid = c.get("section_id")
                if mid:
                    idx = self.mine_combo.findData(mid)
                    if idx >= 0:
                        self.mine_combo.setCurrentIndex(idx)
                self._on_mine_changed()
                if sid:
                    idx = self.section_combo.findData(sid)
                    if idx >= 0:
                        self.section_combo.setCurrentIndex(idx)

    def _format_total(self):
        s = (self.total_edit.text() or "").strip().replace(" ", "").replace(",", ".")
        if not s:
            return
        try:
            v = float(s)
            self.total_edit.blockSignals(True)
            self.total_edit.setText(format_number_for_edit(v))
            self.total_edit.blockSignals(False)
        except ValueError:
            pass

    def _on_mine_changed(self):
        self.section_combo.clear()
        self.section_combo.addItem("—", None)
        mid = self.mine_combo.currentData()
        if mid:
            for sid, _, sname in db.list_sections(mine_id=mid):
                self.section_combo.addItem(sname, sid)

    def on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите название договора.")
            return
        total = to_float(self.total_edit.text())
        contractor = self.contractor_edit.text().strip()
        start = self.start_date_edit.text().strip()
        end = self.end_date_edit.text().strip()
        mine_id = self.mine_combo.currentData()
        section_id = self.section_combo.currentData()
        note = self.note_edit.toPlainText().strip()
        if self.contract_id:
            db.update_service_contract(self.contract_id, name, contractor, total, start or None, end or None, mine_id, section_id, note)
        else:
            db.create_service_contract(name, contractor, total, start or None, end or None, mine_id, section_id, note)
        self.accept()
