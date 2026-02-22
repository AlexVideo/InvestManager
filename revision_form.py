# revision_form.py
from PyQt6 import QtWidgets
from PyQt6.QtCore import QDate
import db
import utils  # для форматирования суммы и внутренних проверок
from utils import to_float
from theme import apply_dialog_theme
import doc_generator

class RevisionDialog(QtWidgets.QDialog):
    def __init__(self, target_project_id: int, parent=None,
                 record_id: int | None = None, edit_mode: bool = False):
        super().__init__(parent)
        self.target_project_id = target_project_id
        self.record_id = record_id
        self.edit_mode = edit_mode
        self.setWindowTitle("Ревизия бюджета" + (" — редактирование" if edit_mode else ""))
        apply_dialog_theme(self)

        # Поля
        self.source_combo = QtWidgets.QComboBox()
        self.available_lbl = QtWidgets.QLabel("Доступно: —")
        self.amount_edit = QtWidgets.QLineEdit()
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.note_edit = QtWidgets.QPlainTextEdit()
        self.memo_chk = QtWidgets.QCheckBox("Сразу сформировать проект служебной записки")
        self.memo_chk.setChecked(False)

        # Форма
        form = QtWidgets.QFormLayout()
        form.addRow("Источник:", self.source_combo)
        if not self.edit_mode:
            # строка с доступной суммой показывается только в режиме создания
            form.addRow("", self.available_lbl)
        form.addRow("Сумма:", self.amount_edit)
        form.addRow("Дата:", self.date_edit)
        form.addRow("Комментарий:", self.note_edit)

        # Кнопки
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)

        # Размещение
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        if not self.edit_mode:
            layout.addWidget(self.memo_chk)
        layout.addWidget(btns)

        # Инициализация
        if self.edit_mode:
            self._load_edit()
        else:
            self._fill_sources()
            self.source_combo.currentIndexChanged.connect(self._update_available)
            self._update_available()

    # ------- helpers
    def _fill_sources(self):
        self.source_combo.clear()
        for pid, name, budget, comment, created_at, _out, _mine, _section in db.list_projects():
            if pid == self.target_project_id:
                continue
            self.source_combo.addItem(name, pid)

    def _load_edit(self):
        r = db.get_revision(self.record_id)
        if not r:
            return
        # в режиме редактирования участников менять нельзя — показываем одним полем
        src = db.get_project(r["source_project_id"])[1]
        dst = db.get_project(r["target_project_id"])[1]
        self.source_combo.addItem(f"{src}  →  {dst}", r["source_project_id"])
        self.source_combo.setEnabled(False)
        self.amount_edit.setText(str(r["amount"]))
        y, m, d = map(int, r["date"].split("-"))
        self.date_edit.setDate(QDate(y, m, d))
        self.note_edit.setPlainText(r["note"] or "")
        self.memo_chk.setVisible(False)

    def _update_available(self):
        pid = self.source_combo.currentData()
        if pid is None:
            self.available_lbl.setText("Доступно: —")
            return
        st = db.compute_project_status(int(pid))
        self.available_lbl.setText(f"Доступно: {utils.money(st['have'])}")

    # ------- actions
    def on_accept(self):
        amt = to_float(self.amount_edit.text())
        if amt <= 0:
            QtWidgets.QMessageBox.warning(self, "Ревизия", "Введите сумму больше нуля.")
            return

        date = self.date_edit.date().toString("yyyy-MM-dd")
        note = self.note_edit.toPlainText().strip()

        if self.edit_mode:
            # редактирование существующей ревизии (участников не меняем)
            db.update_revision(self.record_id, amt, date, note)
            self.accept()
            return

        # режим создания — проверяем доступный остаток источника
        src_id = self.source_combo.currentData()
        if src_id is None:
            QtWidgets.QMessageBox.warning(self, "Ревизия", "Выберите источник.")
            return

        src_status = db.compute_project_status(int(src_id))
        if amt > src_status["have"] + 1e-6:
            QtWidgets.QMessageBox.warning(
                self,
                "Ревизия",
                f"Недостаточно средств в источнике.\nДоступно: {utils.money(src_status['have'])}"
            )
            return

        try:
            db.record_revision(int(src_id), self.target_project_id, amt, date, note)
        except ValueError as e:
            # Доп. защита на уровне БД (если что-то изменилось между проверкой и записью)
            QtWidgets.QMessageBox.warning(self, "Ревизия", str(e))
            return

        if self.memo_chk.isChecked():
            src = db.get_project(int(src_id))
            dst = db.get_project(self.target_project_id)
            path = doc_generator.generate_revision_memo(
                src_project=src[1],
                dst_project=dst[1],
                amount=amt,
                date=date,
                note=note
            )
            QtWidgets.QMessageBox.information(self, "Служебная записка", f"Черновик создан:\n{path}")

        self.accept()
