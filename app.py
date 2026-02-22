# app.py
import sys
import os
from PyQt6 import QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSettings
import db
from main_window import MainWindow

def app_dir() -> str:
    """Папка приложения (рядом с .py в dev и рядом с .exe в сборке)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(*parts) -> str:
    """
    Путь к ресурсам (иконкам и т.п.) — работает и в onefile (PyInstaller),
    и в onedir/разработке.
    """
    base = getattr(sys, "_MEIPASS", app_dir())
    return os.path.join(base, *parts)

def main():
    # Рабочая директория = папка приложения (чтобы data/ создавалась рядом с exe)
    os.chdir(app_dir())

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Invest Manager")
    app.setOrganizationName("InvestTools")
    app.setOrganizationDomain("invest.local")

    # Глобальная иконка для всех окон и панели задач (в сборке — из bundle, в dev — из папки проекта)
    icon_file = resource_path("assets", "Invest.ico")
    if not os.path.exists(icon_file):
        icon_file = os.path.join(app_dir(), "assets", "Invest.ico")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    # --- Выбор активной БД ДО любых вызовов db.* ---
    settings = QSettings()
    last_db = settings.value("db/last_path", "", str)

    chosen_path = None
    new_db_type = None  # при создании новой базы: "invest" или "services"
    if last_db and os.path.exists(last_db):
        # Последняя база существует — используем её
        chosen_path = last_db
    else:
        # Предложить пользователю: открыть существующую или создать новую
        box = QtWidgets.QMessageBox()
        box.setWindowTitle("База данных")
        box.setText("Выберите действие с базой данных:")
        open_btn = box.addButton("Открыть существующую…", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        new_btn  = box.addButton("Создать новую…",       QtWidgets.QMessageBox.ButtonRole.ActionRole)
        cancel_btn = box.addButton("Отмена",             QtWidgets.QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is open_btn:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Открыть базу SQLite", filter="SQLite DB (*.db);;Все файлы (*.*)"
            )
            if not path:
                return  # отменили — ничего не создаём
            chosen_path = path
            settings.setValue("db/last_path", os.path.abspath(path))

        elif clicked is new_btn:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                None, "Создать новую базу", "budget.db", "SQLite DB (*.db)"
            )
            if not path:
                return
            # Выбор типа базы: инвест-проекты (товары) или услуги/работы
            type_box = QtWidgets.QMessageBox(None)
            type_box.setWindowTitle("Тип базы")
            type_box.setText("Что создаём?")
            invest_btn = type_box.addButton("Инвест-проекты (товары)", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            services_btn = type_box.addButton("Услуги и работы", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            cancel_type_btn = type_box.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)
            type_box.exec()
            clicked_type = type_box.clickedButton()
            if clicked_type is cancel_type_btn:
                return
            new_db_type = "invest" if clicked_type is invest_btn else "services"
            chosen_path = path
            settings.setValue("db/last_path", os.path.abspath(path))

        else:
            return  # «Отмена» — выходим, ничего не создавая

    while True:
        try:
            db.set_db_path(chosen_path)
            db.ensure_data_dirs()
            if new_db_type:
                db.init_db(db_type=new_db_type)
            else:
                db.init_db()
            break
        except Exception as e:
            msg = db._format_db_error(e) if hasattr(db, "_format_db_error") else str(e)
            settings.setValue("db/last_path", "")  # чтобы при следующем запуске не открывать сломанную базу
            QtWidgets.QMessageBox.critical(
                None, "База данных",
                f"Не удалось открыть базу:\n{msg}\n\nВыберите другой файл или создайте новую базу."
            )
            # Повторно показать выбор
            box = QtWidgets.QMessageBox()
            box.setWindowTitle("База данных")
            box.setText("Выберите действие с базой данных:")
            open_btn = box.addButton("Открыть существующую…", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            new_btn = box.addButton("Создать новую…", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            quit_btn = box.addButton("Выход", QtWidgets.QMessageBox.ButtonRole.RejectRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked is quit_btn:
                return
            if clicked is open_btn:
                path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    None, "Открыть базу SQLite", filter="SQLite DB (*.db);;Все файлы (*.*)"
                )
                if not path:
                    return
                chosen_path = path
                new_db_type = None
                settings.setValue("db/last_path", os.path.abspath(path))
            else:
                path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    None, "Создать новую базу", "budget.db", "SQLite DB (*.db)"
                )
                if not path:
                    return
                type_box = QtWidgets.QMessageBox(None)
                type_box.setWindowTitle("Тип базы")
                type_box.setText("Что создаём?")
                invest_btn = type_box.addButton("Инвест-проекты (товары)", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                services_btn = type_box.addButton("Услуги и работы", QtWidgets.QMessageBox.ButtonRole.ActionRole)
                cancel_type_btn = type_box.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)
                type_box.exec()
                clicked_type = type_box.clickedButton()
                if clicked_type is cancel_type_btn:
                    return
                new_db_type = "invest" if clicked_type is invest_btn else "services"
                chosen_path = path
                settings.setValue("db/last_path", os.path.abspath(path))

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
