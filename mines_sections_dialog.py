# Справочники: рудники и участки (общие для баз товаров и услуг)
from PyQt6 import QtWidgets, QtCore
import db
from theme import apply_dialog_theme


class MinesSectionsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Рудники и участки")
        self.resize(520, 420)
        apply_dialog_theme(self)

        # Левая часть: рудники
        mines_label = QtWidgets.QLabel("Рудники:")
        self.mines_list = QtWidgets.QListWidget()
        self.mines_list.setMinimumWidth(180)
        self.mines_list.currentRowChanged.connect(self._on_mine_selected)
        mines_btns = QtWidgets.QHBoxLayout()
        self.add_mine_btn = QtWidgets.QPushButton("➕ Добавить")
        self.edit_mine_btn = QtWidgets.QPushButton("✏ Изменить")
        self.del_mine_btn = QtWidgets.QPushButton("🗑 Удалить")
        mines_btns.addWidget(self.add_mine_btn)
        mines_btns.addWidget(self.edit_mine_btn)
        mines_btns.addWidget(self.del_mine_btn)
        mines_left = QtWidgets.QVBoxLayout()
        mines_left.addWidget(mines_label)
        mines_left.addWidget(self.mines_list)
        mines_left.addLayout(mines_btns)

        # Правая часть: участки выбранного рудника
        sections_label = QtWidgets.QLabel("Участки в руднике:")
        self.sections_list = QtWidgets.QListWidget()
        self.sections_list.setMinimumWidth(200)
        self.sections_list.currentRowChanged.connect(lambda: self._update_section_buttons())
        sections_btns = QtWidgets.QHBoxLayout()
        self.add_section_btn = QtWidgets.QPushButton("➕ Добавить")
        self.edit_section_btn = QtWidgets.QPushButton("✏ Изменить")
        self.del_section_btn = QtWidgets.QPushButton("🗑 Удалить")
        sections_btns.addWidget(self.add_section_btn)
        sections_btns.addWidget(self.edit_section_btn)
        sections_btns.addWidget(self.del_section_btn)
        sections_right = QtWidgets.QVBoxLayout()
        sections_right.addWidget(sections_label)
        sections_right.addWidget(self.sections_list)
        sections_right.addLayout(sections_btns)

        main = QtWidgets.QHBoxLayout()
        main.addLayout(mines_left)
        main.addLayout(sections_right)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(main)
        close_btn = QtWidgets.QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.add_mine_btn.clicked.connect(self._add_mine)
        self.edit_mine_btn.clicked.connect(self._edit_mine)
        self.del_mine_btn.clicked.connect(self._delete_mine)
        self.add_section_btn.clicked.connect(self._add_section)
        self.edit_section_btn.clicked.connect(self._edit_section)
        self.del_section_btn.clicked.connect(self._delete_section)

        self._refresh_mines()
        self._update_section_buttons()

    def _current_mine_id(self):
        row = self.mines_list.currentRow()
        if row < 0:
            return None
        item = self.mines_list.item(row)
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None

    def _current_section_id(self):
        row = self.sections_list.currentRow()
        if row < 0:
            return None
        item = self.sections_list.item(row)
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None

    def _refresh_mines(self):
        self.mines_list.clear()
        for mid, mname in db.list_mines():
            it = QtWidgets.QListWidgetItem(mname)
            it.setData(QtCore.Qt.ItemDataRole.UserRole, mid)
            self.mines_list.addItem(it)
        self._on_mine_selected()

    def _refresh_sections(self):
        self.sections_list.clear()
        mid = self._current_mine_id()
        if mid is not None:
            for sid, _, sname in db.list_sections(mine_id=mid):
                it = QtWidgets.QListWidgetItem(sname)
                it.setData(QtCore.Qt.ItemDataRole.UserRole, sid)
                self.sections_list.addItem(it)
        self._update_section_buttons()

    def _on_mine_selected(self):
        self._refresh_sections()

    def _update_section_buttons(self):
        has_mine = self._current_mine_id() is not None
        self.add_section_btn.setEnabled(has_mine)
        self.edit_section_btn.setEnabled(has_mine and self._current_section_id() is not None)
        self.del_section_btn.setEnabled(has_mine and self._current_section_id() is not None)

    def _add_mine(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Рудник", "Название рудника:")
        if not ok or not name.strip():
            return
        try:
            db.create_mine(name.strip())
            self._refresh_mines()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def _edit_mine(self):
        mid = self._current_mine_id()
        if mid is None:
            return
        item = self.mines_list.currentItem()
        old = item.text() if item else ""
        name, ok = QtWidgets.QInputDialog.getText(self, "Рудник", "Название рудника:", text=old)
        if not ok or not name.strip():
            return
        try:
            db.update_mine(mid, name.strip())
            self._refresh_mines()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def _delete_mine(self):
        mid = self._current_mine_id()
        if mid is None:
            return
        if QtWidgets.QMessageBox.question(
            self, "Удаление",
            "Удалить рудник и все его участки? У проектов/договоров привязка к этому руднику будет снята."
        ) != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_mine(mid)
            self._refresh_mines()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def _add_section(self):
        mid = self._current_mine_id()
        if mid is None:
            return
        name, ok = QtWidgets.QInputDialog.getText(self, "Участок", "Название участка:")
        if not ok or not name.strip():
            return
        try:
            db.create_section(mid, name.strip())
            self._refresh_sections()
            self._update_section_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def _edit_section(self):
        sid = self._current_section_id()
        if sid is None:
            return
        item = self.sections_list.currentItem()
        old = item.text() if item else ""
        name, ok = QtWidgets.QInputDialog.getText(self, "Участок", "Название участка:", text=old)
        if not ok or not name.strip():
            return
        mid = self._current_mine_id()
        if mid is None:
            return
        try:
            db.update_section(sid, mid, name.strip())
            self._refresh_sections()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))

    def _delete_section(self):
        sid = self._current_section_id()
        if sid is None:
            return
        if QtWidgets.QMessageBox.question(
            self, "Удаление",
            "Удалить участок? Привязка у проектов/договоров будет снята."
        ) != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            db.delete_section(sid)
            self._refresh_sections()
            self._update_section_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))
