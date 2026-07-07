# settings_dialog.py — выпадающая панель настроек: внешний вид, столбцы, рудники, «О программе»
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QPoint, QRect
from theme import set_theme_params, get_dark_qss, apply_dark_theme
from about_dialog import AboutDialog
import app_settings
from column_settings_dialog import ColumnSettingsDialog

from column_settings_dialog import load_column_order, load_column_visible


def _apply_scale_and_theme(scale: str, main_win=None):
    """Применить масштаб и перерисовать тему."""
    new_data = app_settings.load_app_settings()
    new_data["ui_scale"] = scale
    app_settings.save_app_settings(new_data)
    if scale in app_settings.PRESETS:
        font_pt, btn_pad, tooltip_pt = app_settings.PRESETS[scale]
        set_theme_params(font_size_pt=font_pt, button_padding=btn_pad, tooltip_font_size_pt=tooltip_pt)
    else:
        set_theme_params(
            font_size_pt=new_data.get("font_size_pt", 14),
            button_padding=new_data.get("button_padding", "6px 10px"),
            tooltip_font_size_pt=new_data.get("tooltip_font_size_pt", 12),
        )
    qss = get_dark_qss()
    app = QtWidgets.QApplication.instance()
    if app:
        app.setStyleSheet(qss)
    if main_win:
        main_win.setStyleSheet(qss)


class SettingsPopup(QtWidgets.QFrame):
    """Выпадающая панель настроек: комбобокс «Внешний вид» и кнопки (без надписей над ними). Закрывается при нажатии любой кнопки; комбобокс не закрывает."""
    def __init__(self, parent=None, anchor_btn: QtWidgets.QPushButton = None, invest_mode: bool = True):
        super().__init__(parent, QtCore.Qt.WindowType.Popup | QtCore.Qt.WindowType.FramelessWindowHint)
        self._anchor_btn = anchor_btn
        self.invest_mode = invest_mode
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        apply_dark_theme(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        self.ui_scale_combo = QtWidgets.QComboBox()
        self.ui_scale_combo.addItem("Обычный", "normal")
        self.ui_scale_combo.addItem("Компактный (мелкий экран)", "compact")
        self.ui_scale_combo.addItem("Мелкий (маленький экран)", "small")
        current = app_settings.load_app_settings()
        scale = current.get("ui_scale", "normal")
        idx = self.ui_scale_combo.findData(scale)
        if idx >= 0:
            self.ui_scale_combo.setCurrentIndex(idx)
        self.ui_scale_combo.currentIndexChanged.connect(self._on_scale_changed)
        layout.addWidget(self.ui_scale_combo)

        if invest_mode:
            columns_btn = QtWidgets.QPushButton("Порядок и видимость столбцов…")
            columns_btn.clicked.connect(self._open_column_settings)
            layout.addWidget(columns_btn)

        mines_btn = QtWidgets.QPushButton("Рудники и участки…")
        mines_btn.clicked.connect(self._open_mines_sections)
        layout.addWidget(mines_btn)

        about_btn = QtWidgets.QPushButton("Открыть «О программе»…")
        about_btn.clicked.connect(self._open_about)
        layout.addWidget(about_btn)

    def _on_scale_changed(self):
        scale = self.ui_scale_combo.currentData() or "normal"
        main_win = self.parent()
        _apply_scale_and_theme(scale, main_win)

    def _close_popup_and(self, callback):
        self.close()
        QtCore.QTimer.singleShot(0, callback)

    def _open_column_settings(self):
        main_win = self.parent()
        def open_():
            ColumnSettingsDialog(main_win).exec()
            if main_win and hasattr(main_win, "_apply_column_settings"):
                main_win._apply_column_settings()
        self._close_popup_and(open_)

    def _open_mines_sections(self):
        main_win = self.parent()
        def open_():
            from mines_sections_dialog import MinesSectionsDialog
            MinesSectionsDialog(main_win).exec()
        self._close_popup_and(open_)

    def _open_about(self):
        main_win = self.parent()
        def open_():
            AboutDialog(main_win).exec()
        self._close_popup_and(open_)

    def show_popup(self):
        self.adjustSize()
        if self._anchor_btn and self._anchor_btn.isVisible():
            btn = self._anchor_btn
            btn_rect = QRect(btn.mapToGlobal(QPoint(0, 0)), btn.size())
            screen = btn.screen().availableGeometry() if btn.screen() else None
            if not screen:
                from PyQt6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen().availableGeometry()
            # Выравнивание по правой границе кнопки
            x = btn_rect.right() - self.width()
            y = btn_rect.bottom()
            # Не выходить за левую границу экрана
            if x < screen.left():
                x = screen.left()
            # Не выходить за правую границу экрана
            if x + self.width() > screen.right():
                x = screen.right() - self.width()
            # Не выходить за нижнюю границу — при необходимости показать выше кнопки
            if y + self.height() > screen.bottom():
                y = btn_rect.top() - self.height()
            if y < screen.top():
                y = screen.top()
            if y + self.height() > screen.bottom():
                y = screen.bottom() - self.height()
            self.move(x, y)
        self.show()
