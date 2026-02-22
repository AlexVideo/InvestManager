# settings_dialog.py — настройки столбцов таблицы (режим «Инвест») и «О программе»
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSettings
from theme import apply_dialog_theme
from about_dialog import AboutDialog

# Логические столбцы таблицы проектов (индекс = позиция в списке по умолчанию)
COLUMN_IDS = [
    "name", "mine", "section", "budget", "have", "need",
    "marketing", "contract", "remainder", "exec_pct", "out_of_budget"
]
COLUMN_LABELS = [
    "Название", "Рудник", "Участок", "Заложено", "Имеется", "Необходимо",
    "Маркетинг", "Договор", "Остаток", "Исполн. %", "Вне бюджета"
]

SETTINGS_ORDER_KEY = "invest_columns/order"
SETTINGS_VISIBLE_KEY = "invest_columns/visible"


def load_column_order() -> list[int]:
    """Порядок логических индексов (0..10) слева направо."""
    s = QSettings()
    val = s.value(SETTINGS_ORDER_KEY)
    if val is None:
        return list(range(11))
    if isinstance(val, list):
        return [int(x) for x in val if isinstance(x, (int, str)) and str(x).isdigit()][:11]
    s_str = (val or "").strip()
    if not s_str:
        return list(range(11))
    try:
        out = [int(x.strip()) for x in s_str.split(",") if x.strip().isdigit()][:11]
        return out if len(out) == 11 else list(range(11))
    except (ValueError, AttributeError):
        return list(range(11))


def save_column_order(order: list[int]) -> None:
    s = QSettings()
    s.setValue(SETTINGS_ORDER_KEY, [int(x) for x in order])


def load_column_visible() -> list[bool]:
    """Видимость по логическому индексу (0..10)."""
    s = QSettings()
    val = s.value(SETTINGS_VISIBLE_KEY)
    if val is None:
        return [True] * 11
    if isinstance(val, list):
        return [bool(int(x)) if str(x).isdigit() else True for x in val][:11]
    s_str = (val or "").strip()
    if not s_str:
        return [True] * 11
    try:
        out = [x.strip() in ("1", "true", "yes") for x in s_str.replace(";", ",").split(",")][:11]
        return (out + [True] * 11)[:11]
    except (ValueError, AttributeError):
        return [True] * 11


def save_column_visible(visible: list[bool]) -> None:
    s = QSettings()
    s.setValue(SETTINGS_VISIBLE_KEY, [1 if v else 0 for v in visible])


class ColumnItemWidget(QtWidgets.QWidget):
    """Одна строка списка: галочка + название + кнопки Вверх/Вниз."""
    def __init__(self, logical_index: int, label: str, parent=None):
        super().__init__(parent)
        self.logical_index = logical_index
        self.chk = QtWidgets.QCheckBox("Показывать")
        self.chk.setChecked(True)
        self.label = QtWidgets.QLabel(label)
        self.btn_up = QtWidgets.QPushButton("▲")
        self.btn_up.setFixedWidth(28)
        self.btn_down = QtWidgets.QPushButton("▼")
        self.btn_down.setFixedWidth(28)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self.chk)
        layout.addWidget(self.label, 1)
        layout.addWidget(self.btn_up)
        layout.addWidget(self.btn_down)


class SettingsDialog(QtWidgets.QDialog):
    """Диалог настроек: порядок и видимость столбцов, блок «О программе»."""
    def __init__(self, parent=None, invest_mode: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.invest_mode = invest_mode
        apply_dialog_theme(self)

        layout = QtWidgets.QVBoxLayout(self)

        if invest_mode:
            layout.addWidget(QtWidgets.QLabel("<b>Столбцы таблицы</b>"))
            self.order: list[int] = load_column_order()
            self.visible: list[bool] = load_column_visible()
            self.row_widgets: list[ColumnItemWidget] = []

            self.list_widget = QtWidgets.QWidget()
            self.list_layout = QtWidgets.QVBoxLayout(self.list_widget)
            self.list_layout.setContentsMargins(0, 0, 0, 0)
            for i, logical_idx in enumerate(self.order):
                label = COLUMN_LABELS[logical_idx]
                w = ColumnItemWidget(logical_idx, label)
                w.chk.setChecked(self.visible[logical_idx])
                w.btn_up.clicked.connect(lambda checked=False, pos=i: self._move(pos, -1))
                w.btn_down.clicked.connect(lambda checked=False, pos=i: self._move(pos, 1))
                self.row_widgets.append(w)
                self.list_layout.addWidget(w)
            layout.addWidget(self.list_widget)

        layout.addWidget(QtWidgets.QLabel("<b>Рудники и участки</b>"))
        mines_btn = QtWidgets.QPushButton("Рудники и участки…")
        mines_btn.clicked.connect(self._show_mines_sections)
        layout.addWidget(mines_btn)

        layout.addWidget(QtWidgets.QLabel("<b>О программе</b>"))
        about_btn = QtWidgets.QPushButton("Открыть «О программе»…")
        about_btn.clicked.connect(self._show_about)
        layout.addWidget(about_btn)

        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _move(self, visual_pos: int, delta: int):
        new_pos = visual_pos + delta
        if new_pos < 0 or new_pos >= len(self.order):
            return
        self._save_visible_from_widgets()
        self.order[visual_pos], self.order[new_pos] = self.order[new_pos], self.order[visual_pos]
        self._rebuild_list()

    def _save_visible_from_widgets(self):
        for w in self.row_widgets:
            self.visible[w.logical_index] = w.chk.isChecked()

    def _rebuild_list(self):
        # Удаляем виджеты из лэйаута безопасно (takeAt, иначе itemAt может стать None)
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        self.row_widgets.clear()
        for i, logical_idx in enumerate(self.order):
            label = COLUMN_LABELS[logical_idx]
            w = ColumnItemWidget(logical_idx, label)
            w.chk.setChecked(self.visible[logical_idx])
            w.btn_up.clicked.connect(lambda checked=False, pos=i: self._move(pos, -1))
            w.btn_down.clicked.connect(lambda checked=False, pos=i: self._move(pos, 1))
            self.row_widgets.append(w)
            self.list_layout.addWidget(w)

    def _show_mines_sections(self):
        from mines_sections_dialog import MinesSectionsDialog
        MinesSectionsDialog(self).exec()

    def _show_about(self):
        AboutDialog(self).exec()

    def _accept(self):
        if self.invest_mode:
            self._save_visible_from_widgets()
            save_column_order(self.order)
            save_column_visible(self.visible)
        self.accept()
