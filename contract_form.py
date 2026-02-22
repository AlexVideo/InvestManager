# contract_form.py
from PyQt6 import QtWidgets
from PyQt6.QtCore import QDate
import db, os
from utils import to_float
from theme import apply_dialog_theme

class ContractDialog(QtWidgets.QDialog):
    def __init__(self, project_id: int, parent=None, record_id: int | None = None, prefill: dict | None = None):
        super().__init__(parent)
        self.project_id = project_id
        self.record_id = record_id
        self.setWindowTitle("Договор / Контракт" + (" — редактирование" if record_id else ""))
        apply_dialog_theme(self)

        self.amount_edit = QtWidgets.QLineEdit()
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.contractor_edit = QtWidgets.QLineEdit()
        self.file_edit = QtWidgets.QLineEdit()
        self.file_btn = QtWidgets.QPushButton("Файл договора…")
        self.file_btn.clicked.connect(self.pick_file)
        self.file_open_btn = QtWidgets.QPushButton("Открыть файл")
        self.file_open_btn.clicked.connect(self._open_attached_file)
        self.file_open_btn.setVisible(False)
        self.note_edit = QtWidgets.QPlainTextEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Сумма:", self.amount_edit)
        form.addRow("Дата:", self.date_edit)
        form.addRow("Подрядчик (опц.):", self.contractor_edit)
        fr = QtWidgets.QHBoxLayout()
        fr.addWidget(self.file_edit)
        fr.addWidget(self.file_btn)
        fr.addWidget(self.file_open_btn)
        form.addRow("Файл (опц.):", fr)
        form.addRow("Примечание:", self.note_edit)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                          QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)

        self.file_edit.textChanged.connect(self._update_open_file_btn_visibility)

        if self.record_id:
            self._load()
        elif prefill:
            self._apply_prefill(prefill)
        self._update_open_file_btn_visibility()

    def _load(self):
        r = db.get_contract(self.record_id)
        if not r: return
        self.amount_edit.setText(str(r["amount"]))
        y,m,d = map(int, r["date"].split("-")); self.date_edit.setDate(QDate(y,m,d))
        self.contractor_edit.setText(r["contractor"] or "")
        self.file_edit.setText(r["file_path"] or "")
        self.note_edit.setPlainText(r["note"] or "")

    def _apply_prefill(self, prefill: dict):
        """Предзаполнение из последнего договора (сумма, дата, подрядчик, файл, примечание)."""
        self.amount_edit.setText(str(prefill.get("amount", "")))
        date_str = prefill.get("date") or ""
        if date_str:
            parts = date_str.split("-")
            if len(parts) >= 3:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    self.date_edit.setDate(QDate(y, m, d))
                except (ValueError, TypeError):
                    pass
        self.contractor_edit.setText(prefill.get("contractor") or "")
        self.file_edit.setText(prefill.get("file_path") or "")
        self.note_edit.setPlainText(prefill.get("note") or "")

    def _update_open_file_btn_visibility(self):
        path = (self.file_edit.text() or "").strip()
        full = db.resolve_file_path(path) if path else None
        self.file_open_btn.setVisible(bool(full))

    def _open_attached_file(self):
        path = (self.file_edit.text() or "").strip()
        if not path:
            return
        full = db.resolve_file_path(path)
        if not full:
            QtWidgets.QMessageBox.warning(self, "Файл не найден", "Файл отсутствует или был удалён.")
            return
        try:
            os.startfile(full)
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Файл не найден", "Файл не найден: " + full)
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка открытия", f"Не удалось открыть файл: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def pick_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выбрать файл договора")
        if path: self.file_edit.setText(path)

    def on_accept(self):
        amt = to_float(self.amount_edit.text())
        date = self.date_edit.date().toString("yyyy-MM-dd")
        contr = self.contractor_edit.text().strip() or None
        note = self.note_edit.toPlainText().strip()
        file_path = self.file_edit.text().strip() or None
        if file_path:
            abs_path = file_path if os.path.isabs(file_path) else os.path.normpath(os.path.join(db.DATA_DIR, file_path))
            if os.path.isfile(abs_path):
                project_dir = os.path.abspath(db.get_project_files_dir(self.project_id))
                abs_path_n = os.path.abspath(abs_path)
                if not abs_path_n.startswith(project_dir):
                    try:
                        file_path = db.copy_attachment_to_files(abs_path, "contract", self.project_id)
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(self, "Файл", f"Не удалось скопировать файл: {e}")
                        return
                else:
                    file_path = os.path.relpath(abs_path_n, db.DATA_DIR)
            else:
                file_path = None
        if self.record_id:
            db.update_contract(self.record_id, amt, date, contr, file_path, note)
        else:
            db.record_contract(self.project_id, amt, date, contr, file_path, note)
        self.accept()
