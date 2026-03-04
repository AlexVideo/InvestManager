# export_excel.py
# Экспорт данных в Excel (.xlsx): сводная + лист на каждый проект.
# Требуется: pip install openpyxl

from __future__ import annotations
import os
import datetime as _dt

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    _HAS_OPENPYXL = True
except Exception:
    _HAS_OPENPYXL = False

import db
from utils import money

_MAX_SHEETNAME = 31

def _uniq_sheet_name(base: str, used: set[str]) -> str:
    name = base[:_MAX_SHEETNAME] if len(base) > _MAX_SHEETNAME else base
    if name not in used:
        used.add(name); return name
    i = 2
    while True:
        suffix = f"_{i}"
        cut = _MAX_SHEETNAME - len(suffix)
        cand = (base[:cut] if len(base) > cut else base) + suffix
        if cand not in used:
            used.add(cand); return cand
        i += 1

def _autosize(ws):
    widths = {}
    for row in ws.rows:
        for cell in row:
            v = str(cell.value) if cell.value is not None else ""
            widths[cell.column] = max(widths.get(cell.column, 0), len(v))
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = min(max(10, w + 2), 60)

def export_table_to_excel(xlsx_path: str, headers: list[str], rows: list[list]) -> str:
    """
    Экспортирует в Excel одну таблицу: заголовки и строки (только видимые столбцы и отфильтрованные строки в порядке сортировки).
    Возвращает абсолютный путь к файлу.
    """
    if not _HAS_OPENPYXL:
        raise RuntimeError("Не установлен пакет 'openpyxl'. Установите: pip install openpyxl")
    wb = Workbook()
    ws = wb.active
    ws.title = "Сводная"
    head_fill = PatternFill("solid", fgColor="333333")
    head_font = Font(bold=True, color="FFFFFF")
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = head_fill
        cell.font = head_font
    for row in rows:
        ws.append(row)
    _autosize(ws)
    os.makedirs(os.path.dirname(os.path.abspath(xlsx_path)) or ".", exist_ok=True)
    wb.save(xlsx_path)
    return os.path.abspath(xlsx_path)


def export_to_excel(xlsx_path: str) -> str:
    """
    Экспортирует все проекты в Excel:
      - Лист 'Сводная' (Название, Выделено, Имеется, Необходимо, Остаток, Статус) + гиперссылки на листы проектов
      - По листу на каждый проект (сводка + история)
    Возвращает абсолютный путь к файлу. Бросает RuntimeError, если нет openpyxl.
    """
    if not _HAS_OPENPYXL:
        raise RuntimeError("Не установлен пакет 'openpyxl'. Установите: pip install openpyxl")

    wb = Workbook()
    ws_sum = wb.active
    ws_sum.title = "Сводная"

    # Стили
    head_fill = PatternFill("solid", fgColor="333333")
    head_font = Font(bold=True, color="FFFFFF")
    right = Alignment(horizontal="right")
    wrap = Alignment(wrap_text=True)

    # Заголовок сводной
    headers = ["Название", "Выделено", "Имеется", "Необходимо", "Остаток", "Статус", "Вне бюджета", "Рудник", "Участок"]
    ws_sum.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws_sum.cell(row=1, column=c)
        cell.fill = head_fill
        cell.font = head_font

    # Листы проектов
    used_names: set[str] = set()
    summary_rows = []

    projects = db.list_projects()
    for pid, name, base_budget, comment, created_at, out_of_budget, mine_id, section_id, _ in projects:
        st = db.compute_project_status(pid)
        mine_name = db.get_mine_name(mine_id) if mine_id else ""
        section_name = db.get_section_name(section_id) if section_id else ""
        summary_rows.append((pid, name, base_budget, st["have"], st["need"], st["diff"], st["stage"], bool(out_of_budget), mine_name, section_name))

    # сначала создадим все листы проектов, чтобы в сводной можно было проставить корректные гиперссылки
    sheet_map: dict[int, str] = {}
    for pid, name, *_ in summary_rows:
        sheet_name = _uniq_sheet_name(name if name else f"Проект_{pid}", used_names)
        sheet_map[pid] = sheet_name
        ws = wb.create_sheet(title=sheet_name)

        # Заголовок проекта
        ws["A1"] = f"Карточка проекта: {name}"
        ws["A1"].font = Font(bold=True, size=14)

        # Сводка по проекту
        pr = db.get_project(pid)
        base = float(pr[2]) if pr else 0.0
        out_of_budget = bool(pr[5]) if pr and len(pr) > 5 else False
        st = db.compute_project_status(pid)

        ws["A3"] = "Выделено";   ws["B3"] = money(base)
        ws["A4"] = "Имеется";    ws["B4"] = money(st["have"])
        ws["A5"] = "Необходимо"; ws["B5"] = money(st["need"])
        ws["A6"] = "Остаток";    ws["B6"] = money(st["diff"])
        ws["A7"] = "Вне бюджета"; ws["B7"] = "Да" if out_of_budget else "Нет"
        mine_name = db.get_mine_name(pr[6]) if pr and len(pr) > 6 and pr[6] else ""
        section_name = db.get_section_name(pr[7]) if pr and len(pr) > 7 and pr[7] else ""
        ws["A8"] = "Рудник"; ws["B8"] = mine_name or "—"
        ws["A9"] = "Участок"; ws["B9"] = section_name or "—"

        ws["A3"].font = ws["A4"].font = ws["A5"].font = ws["A6"].font = ws["A7"].font = ws["A8"].font = ws["A9"].font = Font(bold=True)

        # История
        ws["A11"] = "История по датам"
        ws["A11"].font = Font(bold=True)
        ws.append(["Дата", "Тип", "Сумма", "Комментарий", "Файл"])

        for c in range(1, 6):
            cell = ws.cell(row=12, column=c)
            cell.fill = head_fill
            cell.font = head_font

        events = db.get_project_timeline(pid)
        r = 13
        for ev in events:
            ws.cell(row=r, column=1, value=ev["date"])
            ws.cell(row=r, column=2, value=ev["type"])
            amt_cell = ws.cell(row=r, column=3, value=ev["amount"])
            ws.cell(row=r, column=4, value=ev.get("note") or "")
            ws.cell(row=r, column=5, value=ev.get("file_path") or "")
            amt_cell.alignment = right
            r += 1

        # оформление
        _autosize(ws)

    # Заполнение сводной + гиперссылки
    for row_idx, (pid, name, base, have, need, diff, stage, out_of_budget, mine_name, section_name) in enumerate(summary_rows, start=2):
        ws_sum.cell(row=row_idx, column=1, value=name or f"Проект {pid}")
        ws_sum.cell(row=row_idx, column=2, value=base)
        ws_sum.cell(row=row_idx, column=3, value=have)
        ws_sum.cell(row=row_idx, column=4, value=need)
        ws_sum.cell(row=row_idx, column=5, value=diff)
        ws_sum.cell(row=row_idx, column=6, value=stage)
        ws_sum.cell(row=row_idx, column=7, value="Вне бюджета" if out_of_budget else "Бюджет")
        ws_sum.cell(row=row_idx, column=8, value=mine_name or "")
        ws_sum.cell(row=row_idx, column=9, value=section_name or "")

        link_cell = ws_sum.cell(row=row_idx, column=1)
        target_sheet = sheet_map.get(pid)
        if target_sheet:
            link_cell.hyperlink = f"#'{target_sheet}'!A1"
            link_cell.style = "Hyperlink"

        for c in (2, 3, 4, 5, 8, 9):
            ws_sum.cell(row=row_idx, column=c).alignment = right

    _autosize(ws_sum)

    # Сохранение
    os.makedirs(os.path.dirname(os.path.abspath(xlsx_path)), exist_ok=True)
    wb.save(xlsx_path)
    return os.path.abspath(xlsx_path)


if __name__ == "__main__":
    # Простой ручной тест: export_excel.py -> data/export_YYYYMMDD.xlsx
    ts = _dt.date.today().strftime("%Y%m%d")
    out = os.path.join("data", f"export_{ts}.xlsx")
    print("Export to:", export_to_excel(out))
