# add_project_form.py
from PyQt6 import QtWidgets
import db
from utils import to_float, format_number_for_edit
from theme import apply_dialog_theme

class AddProjectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить статью")
        apply_dialog_theme(self)

        self.name_edit = QtWidgets.QLineEdit()
        self.budget_edit = QtWidgets.QLineEdit()
        self.budget_edit.setPlaceholderText("Напр.: 20 000 000")
        self.budget_edit.editingFinished.connect(self._format_budget)
        self.comment_edit = QtWidgets.QPlainTextEdit()
        self.out_of_budget_chk = QtWidgets.QCheckBox("Вне бюджета")
        self.out_of_budget_chk.setChecked(False)
        self.mine_combo = QtWidgets.QComboBox()
        self.mine_combo.addItem("—", None)
        for mid, mname in db.list_mines():
            self.mine_combo.addItem(mname, mid)
        self.mine_combo.currentIndexChanged.connect(self._on_mine_changed)
        self.section_combo = QtWidgets.QComboBox()
        self.section_combo.addItem("—", None)

        form = QtWidgets.QFormLayout()
        form.addRow("Название:", self.name_edit)
        form.addRow("Выделено (бюджет):", self.budget_edit)
        form.addRow("Рудник:", self.mine_combo)
        form.addRow("Участок:", self.section_combo)
        form.addRow("Примечание:", self.comment_edit)
        form.addRow("", self.out_of_budget_chk)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)

    def _on_mine_changed(self):
        self.section_combo.clear()
        self.section_combo.addItem("—", None)
        mid = self.mine_combo.currentData()
        if mid:
            for sid, _, sname in db.list_sections(mine_id=mid):
                self.section_combo.addItem(sname, sid)

    def _format_budget(self):
        """После выхода из поля показываем число с разрядностью (1 000 000)."""
        s = (self.budget_edit.text() or "").strip().replace(" ", "").replace(",", ".")
        if not s:
            return
        try:
            v = float(s)
            self.budget_edit.blockSignals(True)
            self.budget_edit.setText(format_number_for_edit(v))
            self.budget_edit.blockSignals(False)
        except ValueError:
            pass

    def on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите название статьи.")
            return
        budget = to_float(self.budget_edit.text())
        comment = self.comment_edit.toPlainText().strip()
        out_of_budget = self.out_of_budget_chk.isChecked()
        mine_id = self.mine_combo.currentData()
        section_id = self.section_combo.currentData()
        db.create_project(name, budget, comment, out_of_budget, mine_id=mine_id, section_id=section_id)
        self.accept()
