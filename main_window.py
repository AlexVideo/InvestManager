# main_window.py
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import QSettings      # ← ДОБАВИТЬ
import os                                # ← ДОБАВИТЬ

import db
import export_excel

from utils import money, to_float, format_number_for_edit
from theme import apply_dark_theme
from add_project_form import AddProjectDialog
from about_dialog import AboutDialog
from settings_dialog import SettingsDialog, load_column_order, load_column_visible
from project_card import ProjectCard  # ⬅ импортируй вверху
from bulk_import import BulkImportDialog

# Ключи настроек строки состояния (какие пункты показывать). По умолчанию все True.
STATUS_BAR_KEYS = ("budget", "contract", "remainder", "pct", "need", "have", "count", "over_budget")
STATUS_BAR_PREFIX = "status_bar/"

def _load_status_bar_visible() -> dict:
    s = QSettings()
    out = {}
    for k in STATUS_BAR_KEYS:
        v = s.value(STATUS_BAR_PREFIX + k)
        if v is None:
            out[k] = True
        elif isinstance(v, bool):
            out[k] = v
        else:
            out[k] = str(v).lower() in ("1", "true", "yes")
    return out

def _save_status_bar_visible(visible: dict):
    s = QSettings()
    for k, v in visible.items():
        s.setValue(STATUS_BAR_PREFIX + k, v)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invest Manager")
        self.resize(980, 620)
        apply_dark_theme(self)
        if db.get_db_type() == "services":
            self._db_type = "services"
            self._build_services_ui()
            return
        self._db_type = "invest"
        self._build_invest_ui()

    def _build_services_ui(self):
        """Интерфейс для базы «Услуги и работы»: список договоров, акты в карточке."""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        top = QtWidgets.QHBoxLayout()
        self.add_contract_btn = QtWidgets.QPushButton("➕ Добавить договор")
        self.refresh_btn = QtWidgets.QPushButton("⟳ Обновить")
        self.db_btn = QtWidgets.QPushButton("🗂 База…")
        self.about_btn = QtWidgets.QPushButton("⚙ Настройки")
        top.addWidget(self.add_contract_btn)
        top.addWidget(self.db_btn)
        top.addWidget(self.refresh_btn)
        top.addStretch(1)
        top.addWidget(self.about_btn)
        layout.addLayout(top)
        self.services_table = QtWidgets.QTableWidget(0, 6)
        self.services_table.setHorizontalHeaderLabels(["Название", "Контрагент", "Сумма договора", "Списано", "Остаток", "Рудник"])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.services_table)
        self.add_contract_btn.clicked.connect(self._services_add_contract)
        self.refresh_btn.clicked.connect(self._services_refresh)
        self.db_btn.clicked.connect(self._show_db_menu)
        self.about_btn.clicked.connect(self._open_settings)
        self.services_table.cellDoubleClicked.connect(self._services_open_contract_card)
        self._services_refresh()
        self._apply_db_title_services()

    def _services_refresh(self):
        rows = db.list_service_contracts()
        self.services_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            cid, name, contractor, total, start, end, mine_id, section_id, note, created = row
            tot = db.get_service_contract_totals(cid)
            mine_name = db.get_mine_name(mine_id) if mine_id else ""
            self.services_table.setItem(r, 0, QtWidgets.QTableWidgetItem(name))
            self.services_table.setItem(r, 1, QtWidgets.QTableWidgetItem(contractor or ""))
            self.services_table.setItem(r, 2, QtWidgets.QTableWidgetItem(money(tot["total"])))
            self.services_table.setItem(r, 3, QtWidgets.QTableWidgetItem(money(tot["spent"])))
            self.services_table.setItem(r, 4, QtWidgets.QTableWidgetItem(money(tot["remaining"])))
            self.services_table.setItem(r, 5, QtWidgets.QTableWidgetItem(mine_name))
            self.services_table.item(r, 0).setData(QtCore.Qt.ItemDataRole.UserRole, cid)
        self.services_table.setAlternatingRowColors(True)

    def _services_add_contract(self):
        from service_contract_form import ServiceContractDialog
        if ServiceContractDialog(self).exec():
            self._services_refresh()

    def _services_open_contract_card(self, row: int, col: int):
        item = self.services_table.item(row, 0)
        cid = item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None
        if cid is None:
            return
        from service_contract_card import ServiceContractCard
        dlg = ServiceContractCard(cid, self)
        dlg.exec()
        self._services_refresh()

    def _apply_db_title_services(self):
        try:
            path = db.get_db_path()
            base = os.path.basename(path)
            self.setWindowTitle(f"Invest Manager — Услуги — [{base}]")
        except Exception:
            self.setWindowTitle("Invest Manager — Услуги")

    def _build_invest_ui(self):
        """Интерфейс для базы «Инвест-проекты»."""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.add_btn = QtWidgets.QPushButton("➕ Добавить статью")
        self.import_btn = QtWidgets.QPushButton("📥 Импорт проектов")
        self.refresh_btn = QtWidgets.QPushButton("⟳ Обновить")
        self.about_btn = QtWidgets.QPushButton("⚙ Настройки")
        self.export_btn = QtWidgets.QPushButton("📤 Экспорт в Excel")
        self.db_btn = QtWidgets.QPushButton("🗂 База…")  # ← ДОБАВИТЬ


        

        top_bar = QtWidgets.QHBoxLayout()
        top_bar.addWidget(self.add_btn)
        top_bar.addWidget(self.db_btn)  # ← ДОБАВИТЬ
        top_bar.addWidget(self.import_btn)
        top_bar.addWidget(self.export_btn) 
        top_bar.addWidget(self.refresh_btn)   # ← новая кнопка
        top_bar.addStretch(1)
        top_bar.addWidget(self.about_btn)


        

        # Таблица: 11 столбцов (+ Заложено изначально, Исполн. %)
        self.TABLE_HEADERS = [
            "Название", "Рудник", "Участок", "Заложено", "Имеется", "Необходимо",
            "Маркетинг", "Договор", "Остаток", "Исполн. %", "Вне бюджета"
        ]
        self.table = QtWidgets.QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._sort_column = -1
        self._sort_order = QtCore.Qt.SortOrder.AscendingOrder
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for c in range(1, 11):
            self.table.horizontalHeader().setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_ctx_menu)
        self.table.setAlternatingRowColors(True)

        # Строка фильтров: название — текст; суммы — выпадающие меню с ОТ/ДО и кнопкой «Применить»; вне бюджета — выпадающий список
        filter_row = QtWidgets.QHBoxLayout()
        filter_row.addWidget(QtWidgets.QLabel("Фильтр:"))

        self.filter_name_edit = QtWidgets.QLineEdit()
        self.filter_name_edit.setPlaceholderText("Название")
        self.filter_name_edit.setClearButtonEnabled(True)
        self.filter_name_edit.setMinimumWidth(120)
        self.filter_name_edit.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_name_edit)

        self.filter_from_vals = [None] * 7
        self.filter_to_vals = [None] * 7
        num_labels = ["Заложено", "Имеется", "Необходимо", "Маркетинг", "Договор", "Остаток", "Исполн. %"]
        self.filter_range_buttons = []
        for col in range(7):
            btn = QtWidgets.QToolButton()
            btn.setText(f"{num_labels[col]} ▾")
            btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            btn.setMinimumWidth(100)
            menu = QtWidgets.QMenu(self)
            menu.aboutToShow.connect(lambda c=col: self._update_range_edits(c))
            w = QtWidgets.QWidget()
            layout_popup = QtWidgets.QFormLayout(w)
            le_from = QtWidgets.QLineEdit()
            le_from.setPlaceholderText("мин")
            le_from.setMaximumWidth(120)
            le_to = QtWidgets.QLineEdit()
            le_to.setPlaceholderText("макс")
            le_to.setMaximumWidth(120)
            layout_popup.addRow("ОТ:", le_from)
            layout_popup.addRow("ДО:", le_to)
            reset_btn = QtWidgets.QPushButton("Сбросить фильтр")
            layout_popup.addRow(reset_btn)
            widget_action = QtWidgets.QWidgetAction(menu)
            widget_action.setDefaultWidget(w)
            menu.addAction(widget_action)
            le_from.textChanged.connect(lambda t, col_idx=col, f=le_from, to=le_to: self._on_range_filter_changed(col_idx, f, to))
            le_to.textChanged.connect(lambda t, col_idx=col, f=le_from, to=le_to: self._on_range_filter_changed(col_idx, f, to))
            le_from.editingFinished.connect(lambda col_idx=col, f=le_from: self._format_range_edit(f))
            le_to.editingFinished.connect(lambda col_idx=col, t=le_to: self._format_range_edit(t))
            reset_btn.clicked.connect(lambda checked, col_idx=col, m=menu: self._reset_range_filter(col_idx, m))
            btn.setMenu(menu)
            self.filter_range_buttons.append((btn, le_from, le_to))
            filter_row.addWidget(btn)

        self.filter_out_combo = QtWidgets.QComboBox()
        self.filter_out_combo.setMinimumWidth(110)
        self.filter_out_combo.addItems(["—", "По бюджету", "Вне бюджета"])
        self.filter_out_combo.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_out_combo)

        reset_all_btn = QtWidgets.QPushButton("Сбросить все фильтры")
        reset_all_btn.clicked.connect(self._reset_all_filters)
        filter_row.addWidget(reset_all_btn)

        filter_widget = QtWidgets.QWidget()
        filter_widget.setLayout(filter_row)

        # Строка состояния: настраиваемые пункты (правый клик — настройка)
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("padding: 6px; font-weight: bold;")
        self.status_label.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.status_label.customContextMenuRequested.connect(self._on_status_bar_context_menu)
        self._status_totals = {}  # заполняется в refresh()

        # Сборка лэйаута
        layout = QtWidgets.QVBoxLayout(central)
        layout.addLayout(top_bar)
        layout.addWidget(filter_widget)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        # Сигналы
        self.add_btn.clicked.connect(self.add_project)
        self.import_btn.clicked.connect(self.on_import_projects)
        self.refresh_btn.clicked.connect(self.refresh)
        self.export_btn.clicked.connect(self.on_export_excel)
        self.about_btn.clicked.connect(self._open_settings)
        self.table.cellDoubleClicked.connect(self.open_project_card)
        self.db_btn.clicked.connect(self._show_db_menu)  # ← ДОБАВИТЬ


        # Загрузка
        self.refresh()
        self._apply_column_settings()
        self._apply_db_title()  # ← ДОБАВИТЬ
        self._show_opened_toast()



    def refresh(self):
        rows = db.list_projects()
        self.table.setRowCount(len(rows))
        total_budget = 0.0
        total_contract = 0.0
        total_remainder = 0.0
        total_need = 0.0
        total_have = 0.0
        over_budget_count = 0
        for r, (pid, name, base_budget, comment, created_at, out_of_budget, mine_id, section_id) in enumerate(rows):
            status = db.compute_project_status(pid)
            mine_name = db.get_mine_name(mine_id) if mine_id else ""
            section_name = db.get_section_name(section_id) if section_id else ""
            budget_val = float(base_budget) if base_budget is not None else 0.0
            have_val = status["have"] if status["have"] is not None else 0.0
            contract_val = status["contract_amount"] if status["contract_amount"] is not None else 0.0
            total_budget += budget_val
            total_contract += contract_val
            total_remainder += status["diff"] if status["diff"] is not None else 0.0
            total_need += status["need"] if status["need"] is not None else 0.0
            total_have += status["have"] if status["have"] is not None else 0.0
            if status["diff"] is not None and status["diff"] < 0:
                over_budget_count += 1

            name_item = QtWidgets.QTableWidgetItem(name)
            mine_item = QtWidgets.QTableWidgetItem(mine_name)
            section_item = QtWidgets.QTableWidgetItem(section_name)
            budget_item = QtWidgets.QTableWidgetItem(money(budget_val))
            budget_item.setData(QtCore.Qt.ItemDataRole.UserRole, budget_val)
            have_item = QtWidgets.QTableWidgetItem(money(status["have"]))
            need_item = QtWidgets.QTableWidgetItem(money(status["need"]))
            marketing_item = QtWidgets.QTableWidgetItem(money(status["marketing_amount"]) if status["marketing_amount"] is not None else "—")
            contract_item = QtWidgets.QTableWidgetItem(money(status["contract_amount"]) if status["contract_amount"] is not None else "—")
            diff_item = QtWidgets.QTableWidgetItem(money(status["diff"]))
            have_item.setData(QtCore.Qt.ItemDataRole.UserRole, status["have"])
            need_item.setData(QtCore.Qt.ItemDataRole.UserRole, status["need"])
            marketing_item.setData(QtCore.Qt.ItemDataRole.UserRole, status["marketing_amount"] if status["marketing_amount"] is not None else -float("inf"))
            contract_item.setData(QtCore.Qt.ItemDataRole.UserRole, status["contract_amount"] if status["contract_amount"] is not None else -float("inf"))
            diff_item.setData(QtCore.Qt.ItemDataRole.UserRole, status["diff"])
            # Исполн. % = по договорам исполнено / заложено × 100 (сколько от бюджета уже исполнено по договорам)
            if budget_val and contract_val is not None:
                pct = round((contract_val / budget_val) * 100, 1)
                exec_pct_item = QtWidgets.QTableWidgetItem(f"{pct}%")
                exec_pct_item.setData(QtCore.Qt.ItemDataRole.UserRole, pct)
            else:
                exec_pct_item = QtWidgets.QTableWidgetItem("—")
                exec_pct_item.setData(QtCore.Qt.ItemDataRole.UserRole, -float("inf"))
            out_item = QtWidgets.QTableWidgetItem()
            out_item.setFlags(
                (out_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
            out_item.setCheckState(QtCore.Qt.CheckState.Checked if out_of_budget else QtCore.Qt.CheckState.Unchecked)
            out_item.setText("")
            out_item.setData(QtCore.Qt.ItemDataRole.UserRole, pid)

            for it in (budget_item, have_item, need_item, marketing_item, contract_item, diff_item, exec_pct_item):
                it.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, mine_item)
            self.table.setItem(r, 2, section_item)
            self.table.setItem(r, 3, budget_item)
            self.table.setItem(r, 4, have_item)
            self.table.setItem(r, 5, need_item)
            self.table.setItem(r, 6, marketing_item)
            self.table.setItem(r, 7, contract_item)
            self.table.setItem(r, 8, diff_item)
            self.table.setItem(r, 9, exec_pct_item)
            self.table.setItem(r, 10, out_item)

            # Подсветка строки по stage
            stage = status["stage"]
            if stage == "contract":
                self._set_row_bg(r, "#0f3e5a")
            elif stage == "marketing":
                self._set_row_bg(r, "#1f4a3b")
            else:
                self._set_row_bg(r, "#2f2f2f")

            if status["need"] <= status["have"]:
                need_item.setForeground(QBrush(QtCore.Qt.GlobalColor.green))
            else:
                need_item.setForeground(QBrush(QtCore.Qt.GlobalColor.red))
            if status["diff"] >= 0:
                diff_item.setForeground(QBrush(QtCore.Qt.GlobalColor.green))
            else:
                diff_item.setForeground(QBrush(QtCore.Qt.GlobalColor.red))

            name_item.setData(QtCore.Qt.ItemDataRole.UserRole, pid)

        self._status_totals = {
            "budget": total_budget, "contract": total_contract, "remainder": total_remainder,
            "need": total_need, "have": total_have, "over_budget_count": over_budget_count,
        }
        self._apply_sort()
        self._apply_filter()
        self._update_status_label()

    def _set_row_bg(self, row: int, color_hex: str):
        for col in range(self.table.columnCount()):
            it = self.table.item(row, col)
            if it:
                it.setBackground(QBrush(QtCore.Qt.GlobalColor.transparent))
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor(color_hex))

    def _get_sort_key(self, row: int, column: int):
        """Ключ для сортировки. Столбцы 0,1,2 — текст; 3–9 — числа; 10 — галочка."""
        item = self.table.item(row, column)
        if not item:
            return (0, 0.0) if column in (3, 4, 5, 6, 7, 8, 9) else ("",)
        if column in (3, 4, 5, 6, 7, 8, 9):
            val = item.data(QtCore.Qt.ItemDataRole.UserRole)
            try:
                return (0, float(val)) if val is not None else (-float("inf"), 0.0)
            except (TypeError, ValueError):
                return (-float("inf"), 0.0)
        if column == 10:
            return (0, 1 if item.checkState() == QtCore.Qt.CheckState.Checked else 0)
        return (1, (item.text() or "").lower())

    def _on_header_clicked(self, logical_index: int):
        if self._sort_column == logical_index:
            self._sort_order = QtCore.Qt.SortOrder.DescendingOrder if self._sort_order == QtCore.Qt.SortOrder.AscendingOrder else QtCore.Qt.SortOrder.AscendingOrder
        else:
            self._sort_column = logical_index
            self._sort_order = QtCore.Qt.SortOrder.AscendingOrder
        self.table.horizontalHeader().setSortIndicator(logical_index, self._sort_order)
        self._apply_sort()

    def _apply_sort(self):
        """Сортировка по _sort_column и _sort_order (числа — по значению)."""
        n = self.table.rowCount()
        cc = self.table.columnCount()
        if self._sort_column < 0 or n == 0:
            return
        col = self._sort_column
        reverse = self._sort_order == QtCore.Qt.SortOrder.DescendingOrder
        keys = [self._get_sort_key(r, col) for r in range(n)]
        order = sorted(range(n), key=lambda r: keys[r], reverse=reverse)
        # Снимаем ячейки по строкам: после каждой строки удаляем пустую строку, чтобы следующая стала 0
        rows_data = []
        for _ in range(n):
            rows_data.append([self.table.takeItem(0, c) for c in range(cc)])
            self.table.removeRow(0)
        self.table.setRowCount(0)
        for r in order:
            self.table.insertRow(self.table.rowCount())
            row_idx = self.table.rowCount() - 1
            for c in range(cc):
                if rows_data[r][c]:
                    self.table.setItem(row_idx, c, rows_data[r][c])
        self._apply_filter()

    def _update_range_edits(self, col: int):
        """Перед показом меню подставляем в поля ОТ/ДО текущие значения фильтра с разрядностью."""
        _, le_from, le_to = self.filter_range_buttons[col]
        le_from.setText(format_number_for_edit(self.filter_from_vals[col]) if self.filter_from_vals[col] is not None else "")
        le_to.setText(format_number_for_edit(self.filter_to_vals[col]) if self.filter_to_vals[col] is not None else "")

    def _format_range_edit(self, edit: QtWidgets.QLineEdit):
        """После выхода из поля форматируем число с пробелами (разрядность)."""
        s = (edit.text() or "").strip().replace(" ", "").replace(",", ".")
        if not s:
            return
        try:
            v = float(s)
            edit.blockSignals(True)
            edit.setText(format_number_for_edit(v))
            edit.blockSignals(False)
        except ValueError:
            pass

    def _on_range_filter_changed(self, col: int, le_from: QtWidgets.QLineEdit, le_to: QtWidgets.QLineEdit):
        """По мере ввода обновляем фильтр по диапазону и применяем его."""
        s_from = (le_from.text() or "").strip()
        s_to = (le_to.text() or "").strip()
        self.filter_from_vals[col] = to_float(s_from) if s_from else None
        self.filter_to_vals[col] = to_float(s_to) if s_to else None
        self._apply_filter()

    def _reset_range_filter(self, col: int, menu: QtWidgets.QMenu):
        """Сбрасываем фильтр по диапазону для столбца и закрываем меню."""
        self.filter_from_vals[col] = None
        self.filter_to_vals[col] = None
        menu.close()
        self._apply_filter()

    def _reset_all_filters(self):
        """Сбрасываем все фильтры: название, все диапазоны, вне бюджета."""
        self.filter_name_edit.clear()
        for i in range(7):
            self.filter_from_vals[i] = None
            self.filter_to_vals[i] = None
        self.filter_out_combo.blockSignals(True)
        self.filter_out_combo.setCurrentIndex(0)
        self.filter_out_combo.blockSignals(False)
        self._apply_filter()

    def _apply_filter(self):
        """Фильтр: название — подстрока; суммы — диапазон ОТ/ДО (из выпадающих меню); вне бюджета — выпадающий выбор."""
        name_sub = (self.filter_name_edit.text() or "").strip().lower()
        out_idx = self.filter_out_combo.currentIndex()

        for r in range(self.table.rowCount()):
            show = True
            if name_sub:
                item0 = self.table.item(r, 0)
                cell_text = (item0.text() if item0 else "").lower()
                if name_sub not in cell_text:
                    show = False
            if not show:
                self.table.setRowHidden(r, True)
                continue
            for c in range(7):
                item = self.table.item(r, c + 3)
                val = item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None
                try:
                    num = float(val) if val is not None and val != -float("inf") else None
                except (TypeError, ValueError):
                    num = None
                if self.filter_from_vals[c] is not None:
                    if num is None or num < self.filter_from_vals[c]:
                        show = False
                        break
                if show and self.filter_to_vals[c] is not None:
                    if num is None or num > self.filter_to_vals[c]:
                        show = False
                        break
            if not show:
                self.table.setRowHidden(r, True)
                continue
            if out_idx == 1:
                item_out = self.table.item(r, 10)
                if item_out and item_out.checkState() == QtCore.Qt.CheckState.Checked:
                    show = False
            elif out_idx == 2:
                item_out = self.table.item(r, 10)
                if not item_out or item_out.checkState() != QtCore.Qt.CheckState.Checked:
                    show = False
            self.table.setRowHidden(r, not show)
        self._update_status_label()

    def _update_status_label(self):
        """Обновить текст строки состояния по _status_totals и настройкам видимости пунктов."""
        if not getattr(self, "_status_totals", None) or self._db_type != "invest":
            return
        t = self._status_totals
        visible_count = sum(1 for r in range(self.table.rowCount()) if not self.table.isRowHidden(r))
        total_count = self.table.rowCount()
        pct_str = f"{(t['contract'] / t['budget'] * 100):.1f}%" if t["budget"] else "—"
        visible = _load_status_bar_visible()
        parts = []
        if visible.get("budget", True):
            parts.append(f"Заложено: {money(t['budget'])}")
        if visible.get("contract", True):
            parts.append(f"По договорам исполнено: {money(t['contract'])}")
        if visible.get("remainder", True):
            parts.append(f"Остаток: {money(t['remainder'])}")
        if visible.get("need", True):
            parts.append(f"Необходимо: {money(t['need'])}")
        if visible.get("have", True):
            parts.append(f"Имеется: {money(t['have'])}")
        if visible.get("pct", True):
            parts.append(pct_str)
        if visible.get("count", True):
            parts.append(f"Показано: {visible_count} из {total_count}")
        if visible.get("over_budget", True):
            parts.append(f"С перерасходом: {t['over_budget_count']}")
        self.status_label.setText(" | ".join(parts) if parts else "—")

    def _on_status_bar_context_menu(self, _pos):
        """Правый клик по строке состояния — диалог настройки отображаемых пунктов."""
        visible = _load_status_bar_visible()
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Строка состояния — что показывать")
        from theme import apply_dialog_theme
        apply_dialog_theme(dlg)
        layout = QtWidgets.QVBoxLayout(dlg)
        checks = {}
        for key, label in [
            ("budget", "Заложено"),
            ("contract", "По договорам исполнено"),
            ("remainder", "Остаток"),
            ("need", "Необходимо"),
            ("have", "Имеется"),
            ("pct", "Исполн. %"),
            ("count", "Показано N из M"),
            ("over_budget", "Статей с перерасходом"),
        ]:
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(visible.get(key, True))
            checks[key] = cb
            layout.addWidget(cb)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        layout.addWidget(bb)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            visible = {k: checks[k].isChecked() for k in checks}
            _save_status_bar_visible(visible)
            self._update_status_label()

    def add_project(self):
        dlg = AddProjectDialog(self)
        if dlg.exec():
            self.refresh()

    def show_about(self):
        AboutDialog(self).exec()

    def _open_settings(self):
        dlg = SettingsDialog(self, invest_mode=(self._db_type == "invest"))
        if dlg.exec():
            if self._db_type == "invest":
                self._apply_column_settings()

    def _apply_column_settings(self):
        """Применить порядок и видимость столбцов из QSettings (только режим Инвест)."""
        if not hasattr(self, "table") or self.table.columnCount() != 11:
            return
        order = load_column_order()
        visible = load_column_visible()
        for logical in range(11):
            self.table.setColumnHidden(logical, not visible[logical])
        header = self.table.horizontalHeader()
        for to_visual in range(11):
            from_visual = header.visualIndex(order[to_visual])
            if from_visual != to_visual:
                header.moveSection(from_visual, to_visual)

    def open_project_card(self, row: int, col: int):
        item = self.table.item(row, 0)
        pid = item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None
        if pid is None:
            return
        dlg = ProjectCard(pid, self)
        dlg.exec()          # пользователь внёс изменения и закрыл карточку
        self.refresh()      # ← сразу подтягиваем свежие данные в главном окне

    def _current_project_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None

    def _on_ctx_menu(self, pos):
        pid = self._current_project_id()
        if pid is None:
            return
        menu = QtWidgets.QMenu(self)
        act_rename = menu.addAction("Переименовать…")
        act_delete = menu.addAction("Удалить статью…")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_rename:
            self._rename_project(pid)
        elif action == act_delete:
            self._delete_project(pid)

    def _rename_project(self, project_id: int):
        # текущее имя
        name_item = self.table.item(self.table.currentRow(), 0)
        current_name = name_item.text() if name_item else ""
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Переименование",
                                                    "Новое название статьи:", text=current_name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            QtWidgets.QMessageBox.warning(self, "Переименование", "Название не может быть пустым.")
            return
        db.update_project_name(project_id, new_name)
        self.refresh()

    def _delete_project(self, project_id: int):
        # дополнительная проверка перед удалением
        if not db.can_delete_project(project_id):
            counts = db.get_project_activity_counts(project_id)
            QtWidgets.QMessageBox.warning(
                self, "Удаление невозможно",
                "По статье уже есть история операций, удаление запрещено.\n"
                f"Корректировок: {counts['corrections']}, "
                f"Маркетингов: {counts['marketing']}, "
                f"Договоров: {counts['contracts']}, "
                f"Ревизий: {counts['revisions']}."
            )
            return
        if QtWidgets.QMessageBox.question(
            self, "Подтверждение",
            "Удалить статью? Действие необратимо."
        ) != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_project(project_id)
            self.refresh()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Удаление", str(e))
    
    def _get_export_data(self) -> tuple[list[str], list[list]]:
        """Видимые столбцы в визуальном порядке, видимые строки в текущей сортировке. Возвращает (headers, rows)."""
        if not hasattr(self, "table") or self.table.columnCount() != 11:
            return [], []
        header = self.table.horizontalHeader()
        # Видимые столбцы в порядке отображения (слева направо)
        headers = []
        logical_cols = []
        for visual in range(11):
            logical = header.logicalIndex(visual)
            if self.table.isColumnHidden(logical):
                continue
            headers.append(self.TABLE_HEADERS[logical])
            logical_cols.append(logical)
        # Видимые строки
        visible_rows = [r for r in range(self.table.rowCount()) if not self.table.isRowHidden(r)]
        if not visible_rows:
            return headers, []
        # Сортируем как в таблице (_sort_column, _sort_order)
        sort_col = self._sort_column if self._sort_column >= 0 else 0
        reverse = self._sort_order == QtCore.Qt.SortOrder.DescendingOrder
        keys = [self._get_sort_key(r, sort_col) for r in visible_rows]
        order = sorted(range(len(visible_rows)), key=lambda i: keys[i], reverse=reverse)
        sorted_row_indices = [visible_rows[i] for i in order]
        # Собираем данные по строкам
        rows = []
        for r in sorted_row_indices:
            row_data = []
            for logical in logical_cols:
                item = self.table.item(r, logical)
                if logical == 10:
                    val = "Да" if item and item.checkState() == QtCore.Qt.CheckState.Checked else "Нет"
                else:
                    val = (item.text() or "").strip()
                row_data.append(val)
            rows.append(row_data)
        return headers, rows

    def on_export_excel(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import datetime as _dt

        default_name = f"Invest_Export_{_dt.date.today().strftime('%Y%m%d')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить Excel", default_name, "Excel (*.xlsx)")
        if not path:
            return
        try:
            headers, rows = self._get_export_data()
            out = export_excel.export_table_to_excel(path, headers, rows)
            QMessageBox.information(self, "Экспорт в Excel", f"Файл сохранён:\n{out}")
        except RuntimeError as e:
            # например, нет openpyxl
            QMessageBox.warning(self, "Экспорт в Excel",
                                f"{e}\n\nУстановите пакет командой:\n  pip install openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Экспорт в Excel", f"Ошибка экспорта:\n{e}")
    
    def on_import_projects(self):
        dlg = BulkImportDialog(self)
        if dlg.exec():
            self.refresh()

    def _short_path(self, path: str) -> str:
        """Компактное отображение пути: …\\Папка\\имя.db"""
        if not path:
            return "—"
        path = os.path.abspath(path)
        base = os.path.basename(path)
        parent = os.path.basename(os.path.dirname(path))
        # если глубина маленькая — покажем полный
        if len(path) <= 40:
            return path
        return f"…\\{parent}\\{base}"

    def _apply_db_title(self):
        try:
            db_path = db.get_db_path()
        except Exception:
            db_path = ""
        self.setWindowTitle(f"Invest Manager — [{self._short_path(db_path)}]")

    def _show_db_menu(self):
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Открыть существующую базу…")
        act_new  = menu.addAction("Создать новую базу…")
        act_saveas = menu.addAction("Сохранить базу как…")
        menu.addSeparator()


        settings = QSettings()
        current_db = os.path.abspath(db.get_db_path())
        recent = settings.value("db/recent", [], list)
        recent = [p for p in recent if isinstance(p, str) and os.path.exists(p)]
        if recent:
            for p in recent[:8]:
                act = menu.addAction(p)
                # помечаем текущую базу галочкой
                if os.path.abspath(p) == current_db:
                    act.setCheckable(True)
                    act.setChecked(True)
        else:
            a = menu.addAction("(нет недавних)")
            a.setEnabled(False)

        act = menu.exec(self.db_btn.mapToGlobal(self.db_btn.rect().bottomLeft()))
        if not act:
            return
        text = act.text()
        if act == act_open:
            self._db_open_dialog()
        elif act == act_new:
            self._db_new_dialog()
        elif act == act_saveas:
            self._db_save_as_dialog()
        elif os.path.isfile(text):
            self._switch_db(text)

    def _db_open_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Открыть базу SQLite", filter="SQLite DB (*.db);;All files (*.*)"
        )
        if path:
            self._switch_db(path)

    def _db_new_dialog(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Создать новую базу", "budget.db", "SQLite DB (*.db)"
        )
        if not path:
            return
        type_box = QtWidgets.QMessageBox(self)
        type_box.setWindowTitle("Тип базы")
        type_box.setText("Что создаём?")
        invest_btn = type_box.addButton("Инвест-проекты (товары)", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        services_btn = type_box.addButton("Услуги и работы", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        cancel_btn = type_box.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        type_box.exec()
        clicked = type_box.clickedButton()
        if clicked is cancel_btn:
            return
        new_type = "invest" if clicked is invest_btn else "services"
        try:
            db.set_db_path(path)
            db.ensure_data_dirs()
            db.init_db(db_type=new_type)
            self._remember_recent(path)
            self._db_type = new_type
            # Перестроить интерфейс под тип новой базы (сейчас может быть другой тип)
            if new_type == "services":
                self._build_services_ui()
            else:
                self._build_invest_ui()
            if hasattr(self, "_services_refresh"):
                self._apply_db_title_services()
                self._services_refresh()
            else:
                self._apply_db_title()
                self.refresh()
            self._show_opened_toast()
            QtWidgets.QMessageBox.information(self, "База данных", f"Создана база:\n{path}")
        except Exception as e:
            msg = db._format_db_error(e) if hasattr(db, "_format_db_error") else str(e)
            QtWidgets.QMessageBox.critical(self, "База данных", f"Ошибка:\n{msg}")

    def _switch_db(self, path: str, init_new: bool = False):
        try:
            db.set_db_path(path)
            db.ensure_data_dirs()
            db.init_db()
            self._remember_recent(path)
            db_type = db.get_db_type()
            self._db_type = db_type  # иначе после переключения с «Услуги» строка состояния не обновляется
            # Перестроить интерфейс под тип открытой базы
            if db_type == "services":
                self._build_services_ui()
            else:
                self._build_invest_ui()
            try:
                if hasattr(self, "_services_refresh"):
                    self._apply_db_title_services()
                    self._services_refresh()
                else:
                    self._apply_db_title()
                    self.refresh()
            except Exception as e:
                if "service_contracts" in str(e):
                    # В файле записан тип «услуги», но таблицы нет — исправляем тип и показываем как инвест
                    db.set_db_type_meta("invest")
                    self._db_type = "invest"
                    self._build_invest_ui()
                    self._apply_db_title()
                    self.refresh()
                    self._show_opened_toast()
                    QtWidgets.QMessageBox.information(
                        self, "База данных",
                        f"База открыта как «Инвест-проекты».\nАктивная база:\n{path}"
                    )
                    return
                raise
            self._show_opened_toast()
            QtWidgets.QMessageBox.information(self, "База данных", f"Активная база:\n{path}")
        except Exception as e:
            msg = db._format_db_error(e) if hasattr(db, "_format_db_error") else str(e)
            QtWidgets.QMessageBox.critical(self, "База данных", f"Не удалось подключить базу:\n{msg}")

    def _remember_recent(self, path: str):
        settings = QSettings()
        recent = settings.value("db/recent", [], list)
        path = os.path.abspath(path)
        recent = [path] + [p for p in recent if isinstance(p, str) and p != path]
        settings.setValue("db/recent", recent[:12])
        settings.setValue("db/last_path", path)

    def _db_save_as_dialog(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить базу как", "budget_copy.db", "SQLite DB (*.db)"
        )
        if not path:
            return
        try:
            new_path = db.save_db_as(path)
            QtWidgets.QMessageBox.information(self, "Сохранение",
                                            f"База сохранена как:\n{new_path}")
            self._remember_recent(new_path)
            if hasattr(self, "_services_refresh"):
                self._apply_db_title_services()
                self._services_refresh()
            else:
                self._apply_db_title()
                self.refresh()
        except Exception as e:
            msg = db._format_db_error(e) if hasattr(db, "_format_db_error") else str(e)
            QtWidgets.QMessageBox.critical(self, "Сохранение", f"Ошибка:\n{msg}")

    def _show_opened_toast(self):
        try:
            db_path = db.get_db_path()
        except Exception:
            return
        msg = f"Открыта база: {self._short_path(db_path)}"
        # статус-бар создаётся лениво; покажем на 5 секунд
        self.statusBar().showMessage(msg, 5000)






