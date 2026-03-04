# app_settings.py — настройки приложения (внешний вид) в файле data/app_settings.json
import os
import json

_app_dir: str | None = None

# Пресеты: (font_size_pt, button_padding, tooltip_font_size_pt)
PRESETS = {
    "normal": (14, "6px 10px", 12),
    "compact": (12, "4px 6px", 11),
    "small": (10, "3px 5px", 10),
}

DEFAULT_SETTINGS = {
    "ui_scale": "normal",
    "font_size_pt": 14,
    "button_padding": "6px 10px",
    "tooltip_font_size_pt": 12,
}


def set_app_dir(path: str) -> None:
    """Задать папку приложения (вызывать из app.py при старте)."""
    global _app_dir
    _app_dir = path


def get_app_dir() -> str:
    """Папка приложения или текущая при не заданной."""
    return _app_dir or os.getcwd()


def _settings_path() -> str:
    """Путь к файлу настроек: data/app_settings.json в папке приложения."""
    return os.path.join(get_app_dir(), "data", "app_settings.json")


def load_app_settings() -> dict:
    """
    Загрузить настройки из data/app_settings.json.
    При отсутствии файла или ошибке — вернуть копию DEFAULT_SETTINGS.
    """
    path = _settings_path()
    if not os.path.isfile(path):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)
    out = dict(DEFAULT_SETTINGS)
    for key in DEFAULT_SETTINGS:
        if key in data:
            out[key] = data[key]
    return out


def save_app_settings(data: dict) -> None:
    """Сохранить настройки в data/app_settings.json. Папка data создаётся при необходимости."""
    path = _settings_path()
    base = os.path.dirname(path)
    if base:
        os.makedirs(base, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
