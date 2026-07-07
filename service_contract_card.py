# Карточка договора (услуги): данные договора и таблица актов выполненных работ
from PyQt6 import QtWidgets, QtCore
import db
from utils import money, to_float, format_number_for_edit
from theme import apply_dialog_theme


class ServiceContractCard(QtWidgets.QDialog):
    def __init__(self, contract_id: int, parent=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.setWindowTitle("Договор (услуги/работы)")
        self.resize(720, 520)
        apply_dialog_theme(self)

        c = db.get_service_contract(contract_id)
        if not c:
            return
        tot = db.get_service_contract_totals(contract_id)
        mine_name = db.get_mine_name(c.get("mine_id")) if c.get("mine_id") else ""
        section_name = db.get_section_name(c.get("section_id")) if c.get("section_id") else ""

        self.title_lbl = QtWidgets.QLabel(f"Договор: {c['name']}")
        self.title_lbl.setStyleSheet("font-size:14pt;")
        self.total_lbl = QtWidgets.QLabel(f"Сумма договора: {money(tot['total'])}")
        self.spent_lbl = QtWidgets.QLabel(f"Списано всего: {money(tot['spent'])}")
        self.remaining_lbl = QtWidgets.QLabel(f"Остаток: {money(tot['remaining'])}")
        self.mine_lbl = QtWidgets.QLabel(f"Рудник: {mine_name or '—'}")
        self.section_lbl = QtWidgets.QLabel(f"Участок: {section_name or '—'}")

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.title_lbl, 0, 0, 1, 2)
        grid.addWidget(self.total_lbl, 1, 0)
        grid.addWidget(self.spent_lbl, 1, 1)
        grid.addWidget(self.remaining_lbl, 2, 0)
        grid.addWidget(self.mine_lbl, 2, 1)
        grid.addWidget(self.section_lbl, 3, 0)

        self.acts_table = QtWidgets.QTableWidget(0, 5)
        self.acts_table.setHorizontalHeaderLabels(["Период с", "Период по", "Дата акта", "Сумма", ""])
        self.acts_table.horizontalHeader().setStretchLastSection(True)
        self.acts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.acts_table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.acts_table.customContextMenuRequested.connect(self._on_ctx_menu)

        self.add_act_btn = QtWidgets.QPushButton("➕ Добавить акт выполненных работ")
        self.edit_contract_btn = QtWidgets.QPushButton("✏ Редактировать договор")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(grid)
        layout.addWidget(QtWidgets.QLabel("Акты выполненных работ:"))
        layout.addWidget(self.acts_table)
        layout.addWidget(self.add_act_btn)
        layout.addWidget(self.edit_contract_btn)

        self.add_act_btn.clicked.connect(self._add_act)
        self.edit_contract_btn.clicked.connect(self._edit_contract)
        self.refresh()

    def refresh(self):
        tot = db.get_service_contract_totals(self.contract_id)
        self.total_lbl.setText(f"Сумма договора: {money(tot['total'])}")
        self.spent_lbl.setText(f"Списано всего: {money(tot['spent'])}")
        self.remaining_lbl.setText(f"Остаток: {money(tot['remaining'])}")
        c = db.get_service_contract(self.contract_id)
        if c:
            self.mine_lbl.setText(f"Рудник: {db.get_mine_name(c.get('mine_id')) or '—'}")
            self.section_lbl.setText(f"Участок: {db.get_section_name(c.get('section_id')) or '—'}")

        acts = db.list_service_acts(self.contract_id)
        self.acts_table.setRowCount(len(acts))
        for r, a in enumerate(acts):
            self.acts_table.setItem(r, 0, QtWidgets.QTableWidgetItem(a.get("period_start") or ""))
            self.acts_table.setItem(r, 1, QtWidgets.QTableWidgetItem(a.get("period_end") or ""))
            self.acts_table.setItem(r, 2, QtWidgets.QTableWidgetItem(a.get("act_date") or ""))
            amt_item = QtWidgets.QTableWidgetItem(money(a.get("amount", 0)))
            amt_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.acts_table.setItem(r, 3, amt_item)
            self.acts_table.setItem(r, 4, QtWidgets.QTableWidgetItem(str(a.get("id", ""))))
            self.acts_table.item(r, 4).setData(QtCore.Qt.ItemDataRole.UserRole, a.get("id"))
        self.acts_table.setColumnHidden(4, True)
        self.acts_table.setAlternatingRowColors(True)

    def _add_act(self):
        from service_act_form import ServiceActDialog
        if ServiceActDialog(self.contract_id, self).exec():
            self.refresh()

    def _edit_contract(self):
        from service_contract_form import ServiceContractDialog
        if ServiceContractDialog(parent=self, contract_id=self.contract_id).exec():
            c = db.get_service_contract(self.contract_id)
            if c:
                self.title_lbl.setText(f"Договор: {c['name']}")
            self.refresh()

    def _on_ctx_menu(self, pos):
        row = self.acts_table.currentRow()
        if row < 0:
            return
        act_id_item = self.acts_table.item(row, 4)
        act_id = act_id_item.data(QtCore.Qt.ItemDataRole.UserRole) if act_id_item else None
        if act_id is None:
            return
        menu = QtWidgets.QMenu(self)
        act_edit = menu.addAction("Изменить…")
        act_del = menu.addAction("Удалить…")
        action = menu.exec(self.acts_table.viewport().mapToGlobal(pos))
        if action == act_edit:
            from service_act_form import ServiceActDialog
            if ServiceActDialog(self.contract_id, self, act_id=act_id).exec():
                self.refresh()
        elif action == act_del:
            if QtWidgets.QMessageBox.question(self, "Удаление", "Удалить акт?") == QtWidgets.QMessageBox.StandardButton.Yes:
                db.delete_service_act(act_id)
                self.refresh()
