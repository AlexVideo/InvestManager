# project_card.py
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QBrush, QColor, QAction
import os
import db
from utils import money
from theme import apply_dialog_theme
from marketing_form import MarketingDialog
from contract_form import ContractDialog
from correction_form import CorrectionDialog
from revision_form import RevisionDialog
import doc_generator

class ProjectCard(QtWidgets.QDialog):
    def __init__(self, project_id: int, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("Карточка проекта")
        self.resize(940, 660)
        apply_dialog_theme(self)

        p = db.get_project(project_id)
        self.title_lbl = QtWidgets.QLabel(f"Карточка проекта: {p[1] if p else '??'}")
        self.title_lbl.setStyleSheet("font-size:18pt; margin-bottom:6px;")

        self.out_of_budget_chk = QtWidgets.QCheckBox("Вне бюджета")
        self.out_of_budget_chk.blockSignals(True)
        self.out_of_budget_chk.setChecked(bool(p[5]) if p and len(p) > 5 else False)
        self.out_of_budget_chk.blockSignals(False)
        self.out_of_budget_chk.stateChanged.connect(self._on_out_of_budget_changed)
        self.out_of_budget_chk.setToolTip("Редактируется только здесь; в таблице только отображение.")

        self.mine_combo = QtWidgets.QComboBox()
        self.mine_combo.addItem("—", None)
        for mid, mname in db.list_mines():
            self.mine_combo.addItem(mname, mid)
        self.mine_combo.currentIndexChanged.connect(self._on_mine_combo_changed)
        self.section_combo = QtWidgets.QComboBox()
        self.section_combo.addItem("—", None)
        self.section_combo.currentIndexChanged.connect(self._save_mine_section)

        self.allocated_lbl = QtWidgets.QLabel("Выделено: —")
        self.have_lbl      = QtWidgets.QLabel("Имеется: —")
        self.need_lbl      = QtWidgets.QLabel("Необходимо: —")
        self.diff_lbl      = QtWidgets.QLabel("Остаток: —")
        for w in (self.allocated_lbl, self.have_lbl, self.need_lbl, self.diff_lbl):
            w.setStyleSheet("font-size:14pt;")

        summary = QtWidgets.QGridLayout()
        summary.addWidget(self.allocated_lbl, 0, 0)
        summary.addWidget(self.have_lbl,      0, 1)
        summary.addWidget(self.need_lbl,      1, 0)
        summary.addWidget(self.diff_lbl,      1, 1)
        summary.addWidget(self.out_of_budget_chk, 2, 0, 1, 2)
        summary.addWidget(QtWidgets.QLabel("Рудник:"), 3, 0)
        summary.addWidget(self.mine_combo, 3, 1)
        summary.addWidget(QtWidgets.QLabel("Участок:"), 4, 0)
        summary.addWidget(self.section_combo, 4, 1)

        # 6 видимых + 2 скрытых (kind, id)
        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Дата", "Тип", "Сумма", "Комментарий", "Файл", "Кто внёс", "_kind", "_id"])
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnHidden(6, True)
        self.table.setColumnHidden(7, True)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        # контекст-меню
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_ctx_menu)

        self.rev_btn   = QtWidgets.QPushButton("🔁 Ревизия")
        self.mkt_btn   = QtWidgets.QPushButton("📋 Маркетинг")
        self.cor_btn   = QtWidgets.QPushButton("🔧 Корректировка")
        self.ctr_btn   = QtWidgets.QPushButton("📄 Договор")
        self.memo_btn  = QtWidgets.QPushButton("📝 Проект служебной записки")

        actions = QtWidgets.QHBoxLayout()
        for b in (self.rev_btn, self.mkt_btn, self.cor_btn, self.ctr_btn):
            actions.addWidget(b)
        actions.addStretch(1)
        actions.addWidget(self.memo_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.title_lbl)
        layout.addLayout(summary)
        layout.addWidget(self.table)
        layout.addLayout(actions)

        self.rev_btn.clicked.connect(self.on_revision)
        self.mkt_btn.clicked.connect(self.on_marketing)
        self.cor_btn.clicked.connect(self.on_correction)
        self.ctr_btn.clicked.connect(self.on_contract)
        self.memo_btn.clicked.connect(self.on_memo)

        self.refresh()

    def _on_out_of_budget_changed(self, state):
        # state: 0 = Unchecked, 2 = Checked (PyQt6 передаёт int)
        is_checked = (state == QtCore.Qt.CheckState.Checked) or (state == 2)
        db.update_project_out_of_budget(self.project_id, is_checked)

    def _refill_sections(self, mine_id):
        self.section_combo.blockSignals(True)
        self.section_combo.clear()
        self.section_combo.addItem("—", None)
        if mine_id:
            for sid, _, sname in db.list_sections(mine_id=mine_id):
                self.section_combo.addItem(sname, sid)
        self.section_combo.blockSignals(False)

    def _on_mine_combo_changed(self):
        self._refill_sections(self.mine_combo.currentData())
        self._save_mine_section()

    def _save_mine_section(self):
        db.update_project_mine_section(self.project_id, self.mine_combo.currentData(), self.section_combo.currentData())

    def refresh(self):
        pr = db.get_project(self.project_id)
        base = float(pr[2]) if pr else 0.0
        mine_id = pr[6] if pr and len(pr) > 6 else None
        section_id = pr[7] if pr and len(pr) > 7 else None
        self.mine_combo.blockSignals(True)
        idx = self.mine_combo.findData(mine_id)
        self.mine_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.mine_combo.blockSignals(False)
        self._refill_sections(mine_id)
        self.section_combo.blockSignals(True)
        idx = self.section_combo.findData(section_id)
        self.section_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.section_combo.blockSignals(False)
        st = db.compute_project_status(self.project_id)
        self.allocated_lbl.setText(f"Выделено: {money(base)}")
        self.have_lbl.setText(f"Имеется: {money(st['have'])}")
        self.need_lbl.setText(f"Необходимо: {money(st['need'])}")
        self.diff_lbl.setText(f"Остаток: {money(st['diff'])}")

        self.need_lbl.setStyleSheet("color:#9be69b; font-size:14pt;" if st['need'] <= st['have'] else "color:#ff7a7a; font-size:14pt;")
        self.diff_lbl.setStyleSheet("color:#9be69b; font-size:14pt;" if st['diff'] >= 0 else "color:#ff7a7a; font-size:14pt;")

        events = db.get_project_timeline(self.project_id)
        self.table.setRowCount(len(events))
        for r, ev in enumerate(events):
            d = QtWidgets.QTableWidgetItem(ev["date"])
            t = QtWidgets.QTableWidgetItem(ev["type"])
            a = QtWidgets.QTableWidgetItem(money(ev["amount"] if ev["amount"] is not None else 0))
            n = QtWidgets.QTableWidgetItem(ev.get("note") or "")
            f = QtWidgets.QTableWidgetItem(ev.get("file_path") or "")
            who = QtWidgets.QTableWidgetItem(ev.get("added_by") or "")
            k = QtWidgets.QTableWidgetItem(ev["kind"])
            i = QtWidgets.QTableWidgetItem(str(ev["id"]))

            a.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 0, d)
            self.table.setItem(r, 1, t)
            self.table.setItem(r, 2, a)
            self.table.setItem(r, 3, n)
            self.table.setItem(r, 4, f)
            self.table.setItem(r, 5, who)
            self.table.setItem(r, 6, k)  # hidden
            self.table.setItem(r, 7, i)  # hidden

            if ev["type"].startswith("Ревизия"):
                a.setForeground(QBrush(QtCore.Qt.GlobalColor.green if ev.get("sign")== "+" else QtCore.Qt.GlobalColor.red))

        self.table.sortItems(0, QtCore.Qt.SortOrder.DescendingOrder)

    # ---- Контекст-меню
    def _on_ctx_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        kind = self.table.item(row, 6).text() if self.table.item(row, 6) else ""
        rec_id = int(self.table.item(row, 7).text()) if self.table.item(row, 7) else None
        file_path = (self.table.item(row, 4).text() or "").strip() if self.table.item(row, 4) else ""

        menu = QtWidgets.QMenu(self)
        act_edit = QAction("Изменить…", self)
        act_del  = QAction("Удалить…", self)
        act_edit.triggered.connect(lambda: self._edit_record(kind, rec_id))
        act_del.triggered.connect(lambda: self._delete_record(kind, rec_id))
        menu.addAction(act_edit)
        menu.addAction(act_del)
        if file_path:
            act_open = QAction("Открыть файл", self)
            act_open.triggered.connect(lambda: self._open_attachment(file_path))
            menu.addAction(act_open)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_cell_double_clicked(self, row: int, col: int):
        if col == 4:
            it = self.table.item(row, 4)
            path = (it.text() or "").strip() if it else ""
            if path:
                self._open_attachment(path)

    def _open_attachment(self, stored_path: str):
        """Открыть прикреплённый файл в программе по умолчанию (Windows). С обработкой ошибок."""
        if not stored_path or not str(stored_path).strip():
            return
        full = db.resolve_file_path(stored_path)
        if not full:
            QtWidgets.QMessageBox.warning(
                self,
                "Файл не найден",
                "Файл отсутствует или был удалён:\n" + (stored_path or "")
            )
            return
        try:
            os.startfile(full)
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Файл не найден", "Файл не найден: " + full)
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка открытия", f"Не удалось открыть файл: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def _edit_record(self, kind: str, rec_id: int):
        if kind == "marketing":
            dlg = MarketingDialog(self.project_id, self, record_id=rec_id)
        elif kind == "contract":
            dlg = ContractDialog(self.project_id, self, record_id=rec_id)
        elif kind == "correction":
            dlg = CorrectionDialog(self.project_id, self, record_id=rec_id)
        elif kind in ("revision_in", "revision_out"):
            dlg = RevisionDialog(self.project_id, self, record_id=rec_id, edit_mode=True)
        else:
            return
        if dlg.exec():
            self.refresh()

    def _delete_record(self, kind: str, rec_id: int):
        if QtWidgets.QMessageBox.question(self, "Удаление", "Удалить выбранную запись? Это действие необратимо.") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        if kind == "marketing":
            db.delete_marketing(rec_id)
        elif kind == "contract":
            db.delete_contract(rec_id)
        elif kind == "correction":
            db.delete_correction(rec_id)
        elif kind in ("revision_in", "revision_out"):
            db.delete_revision(rec_id)
        self.refresh()

    # ---- Кнопки действий
    def on_marketing(self):
        last = db.get_last_marketing_for_project(self.project_id)
        if last:
            QtWidgets.QMessageBox.warning(
                self,
                "Маркетинг уже проводился",
                "По этой статье маркетинг уже проводился.\nДанные предыдущего маркетинга подставлены в форму — при необходимости измените и сохраните новый маркетинг."
            )
        dlg = MarketingDialog(self.project_id, self, record_id=None, prefill=last)
        if dlg.exec():
            self.refresh()

    def on_contract(self):
        last = db.get_last_contract_for_project(self.project_id)
        if last:
            QtWidgets.QMessageBox.warning(
                self,
                "Договор уже вносился",
                "По этой статье договор уже вносился.\nДанные предыдущего договора подставлены в форму — при необходимости измените и сохраните новый договор."
            )
        dlg = ContractDialog(self.project_id, self, record_id=None, prefill=last)
        if dlg.exec():
            self.refresh()

    def on_correction(self):
        if CorrectionDialog(self.project_id, self).exec():
            self.refresh()

    def on_revision(self):
        if RevisionDialog(self.project_id, self).exec():
            self.refresh()

    def on_memo(self):
        last_rev = db.get_last_revision_for_project(self.project_id)
        if not last_rev:
            QtWidgets.QMessageBox.information(self, "Служебная записка", "Нет ревизий для формирования проекта служебной записки.")
            return
        if last_rev["target_project_id"] == self.project_id:
            src = db.get_project(last_rev["source_project_id"])
            dst = db.get_project(last_rev["target_project_id"])
        else:
            src = db.get_project(last_rev["target_project_id"])
            dst = db.get_project(last_rev["source_project_id"])
        path = doc_generator.generate_revision_memo(
            src_project=src[1], dst_project=dst[1],
            amount=last_rev["amount"], date=last_rev["date"], note=last_rev.get("note") or "",
            project_id=self.project_id
        )
        QtWidgets.QMessageBox.information(self, "Служебная записка", f"Черновик создан:\n{path}")
