# db.py
import os, sqlite3, datetime

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "budget.db")


def _format_db_error(e: Exception) -> str:
    """Понятное сообщение об ошибке при открытии БД."""
    msg = str(e).strip()
    if not msg:
        return "Неизвестная ошибка базы данных."
    if "not a database" in msg.lower() or "file is not a database" in msg.lower():
        return "Файл не является базой данных SQLite или повреждён."
    if "unable to open" in msg.lower() or "could not open" in msg.lower():
        return "Не удалось открыть файл. Проверьте путь и права доступа."
    if "database is locked" in msg.lower() or "locked" in msg.lower():
        return "База занята другим процессом. Закройте другие программы, использующие этот файл."
    if "disk i/o" in msg.lower() or "io error" in msg.lower():
        return "Ошибка чтения/записи диска. Возможно, диск недоступен или повреждён."
    if "no such table" in msg.lower():
        return "В базе нет нужных таблиц. Возможно, это база от другой программы."
    if "corrupt" in msg.lower() or "malformed" in msg.lower():
        return "База данных повреждена."
    return msg

def _recalc_dirs():
    global DATA_DIR, FILES_DIR
    DATA_DIR = os.path.dirname(DB_PATH) or "."
    FILES_DIR = os.path.join(DATA_DIR, "Files")

_recalc_dirs()

import shutil

# Версия схемы БД: при открытии старой базы выполняются миграции от текущей версии до SCHEMA_VERSION
SCHEMA_VERSION = 2


def _get_schema_version(cur) -> int:
    cur.execute("SELECT value FROM _meta WHERE key='schema_version'")
    row = cur.fetchone()
    if not row:
        return 0
    try:
        return int(row[0].strip())
    except (ValueError, TypeError):
        return 0


def _set_schema_version(cur, version: int):
    cur.execute("DELETE FROM _meta WHERE key='schema_version'")
    cur.execute("INSERT INTO _meta (key, value) VALUES ('schema_version', ?)", (str(version),))


def _backup_db():
    """Копия БД перед миграцией (в ту же папку, суффикс .backup_YYYYMMDD_HHMMSS)."""
    if not os.path.isfile(DB_PATH):
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH + f".backup_{stamp}"
    try:
        shutil.copy2(DB_PATH, backup_path)
    except Exception:
        pass


def _migrate_0_to_1(cur):
    """Версия 1: out_of_budget, mine_id, section_id в projects."""
    cur.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cur.fetchall()]
    if "out_of_budget" not in columns:
        cur.execute("ALTER TABLE projects ADD COLUMN out_of_budget INTEGER NOT NULL DEFAULT 0")
    if "mine_id" not in columns:
        cur.execute("ALTER TABLE projects ADD COLUMN mine_id INTEGER REFERENCES mines(id)")
    if "section_id" not in columns:
        cur.execute("ALTER TABLE projects ADD COLUMN section_id INTEGER REFERENCES sections(id)")


def _migrate_1_to_2(cur):
    """Версия 2: added_by в corrections, marketing, contracts, revisions."""
    for table in ("corrections", "marketing", "contracts", "revisions"):
        cur.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cur.fetchall()]
        if "added_by" not in columns:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN added_by TEXT DEFAULT ''")


# Список миграций: индекс i — переход с версии i на i+1
_MIGRATIONS = [_migrate_0_to_1, _migrate_1_to_2]


def _run_migrations(con):
    """Выполнить миграции с текущей версии схемы до SCHEMA_VERSION. Перед первым шагом — бэкап."""
    cur = con.cursor()
    current = _get_schema_version(cur)
    if current >= SCHEMA_VERSION:
        return
    _backup_db()
    for v in range(current, SCHEMA_VERSION):
        _MIGRATIONS[v](cur)
        _set_schema_version(cur, v + 1)
        con.commit()

def save_db_as(new_path: str):
    """Сохранить текущую БД под новым именем (как Save As)."""
    global DB_PATH
    src = DB_PATH
    dst = os.path.abspath(new_path)
    shutil.copy2(src, dst)
    set_db_path(dst)        # переключаемся на новый файл
    ensure_data_dirs()
    init_db()               # убеждаемся, что структура есть
    return dst


def ensure_data_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)

def get_db_basename() -> str:
    """Имя файла базы без расширения, безопасное для имени папки (Files/{этот_имя}/)."""
    name = os.path.splitext(os.path.basename(DB_PATH))[0] or "db"
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip() or "db"

def _safe_foldername(name: str) -> str:
    """Имя, пригодное для папки в Windows (без \\ / : * ? \" < > |)."""
    s = (name or "").strip()
    for c in '\\/:*?"<>|':
        s = s.replace(c, "_")
    return s.strip() or "project"

def get_project_folder_name(project_id: int) -> str:
    """Имя папки проекта: id_Название (уникально и читаемо)."""
    proj = get_project(project_id)
    name = proj[1] if proj else str(project_id)
    return f"{project_id}_{_safe_foldername(name)}"

def get_project_files_dir(project_id: int) -> str:
    """
    Путь к папке файлов проекта: Files/{имя_базы}/{id_НазваниеПроекта}/.
    Папка создаётся при первом обращении. Возвращает абсолютный путь.
    """
    ensure_data_dirs()
    base = get_db_basename()
    folder_name = get_project_folder_name(project_id)
    path = os.path.join(FILES_DIR, base, folder_name)
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)

def get_windows_user() -> str:
    """Имя учётной записи Windows (кто внёс изменения)."""
    try:
        return (os.environ.get("USERNAME") or os.environ.get("USER") or "").strip()
    except Exception:
        return ""

def copy_attachment_to_files(source_path: str, kind: str, project_id: int) -> str:
    """
    Копирует файл в папку проекта Files/{имя_базы}/{id_Название}/. Возвращает путь относительно DATA_DIR.
    kind по-прежнему передаётся для совместимости вызовов, структура папок от него не зависит.
    """
    if not source_path or not os.path.isfile(source_path):
        return ""
    folder = get_project_files_dir(project_id)
    base = os.path.basename(source_path)
    base = "".join(c for c in base if c.isalnum() or c in "._- ()") or "file"
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{project_id}_{stamp}_{base}"
    dst = os.path.join(folder, name)
    try:
        shutil.copy2(source_path, dst)
        return os.path.relpath(dst, DATA_DIR)
    except Exception:
        raise

def resolve_file_path(stored_path: str | None) -> str | None:
    """Преобразует путь из БД (относительный или абсолютный) в абсолютный для открытия. Возвращает None если файл недоступен."""
    if not stored_path or not str(stored_path).strip():
        return None
    p = str(stored_path).strip()
    if os.path.isabs(p):
        return p if os.path.isfile(p) else None
    full = os.path.normpath(os.path.join(DATA_DIR, p))
    return full if os.path.isfile(full) else None

def set_db_path(path: str):
    """Сменить активную БД на произвольный файл .db"""
    global DB_PATH
    DB_PATH = os.path.abspath(path)
    _recalc_dirs()

def get_db_path() -> str:
    return DB_PATH


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def _ensure_meta(cur):
    """Создать таблицу _meta если нет; для старых БД записать db_type=invest."""
    cur.execute("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM _meta WHERE key='db_type'")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO _meta (key, value) VALUES ('db_type', 'invest')")

def get_db_type() -> str:
    """Тип базы: 'invest' (инвест-проекты/товары) или 'services' (услуги и работы)."""
    con = connect()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM _meta WHERE key='db_type'")
    row = cur.fetchone()
    stored = (row[0] if row else "invest").strip() or "invest"
    # Если в _meta указано 'services', но таблицы услуг нет — это старая база товаров
    if stored == "services":
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_contracts'")
        if cur.fetchone() is None:
            con.close()
            return "invest"
    con.close()
    return stored

def set_db_type_meta(value: str):
    """Записать в _meta тип базы ('invest' или 'services'). Нужно для исправления старых БД."""
    con = connect()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("DELETE FROM _meta WHERE key='db_type'")
    cur.execute("INSERT INTO _meta (key, value) VALUES ('db_type', ?)", (value.strip(),))
    con.commit()
    con.close()

def init_db(db_type: str | None = None):
    """
    Инициализация/миграция БД.
    db_type=None: открытие существующей — проверить _meta, применить миграции по типу.
    db_type='invest' или 'services': создание новой базы с выбранным типом.
    """
    con = connect()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM _meta WHERE key='db_type'")
    existing = cur.fetchone()
    existing_type = existing[0].strip() if existing else None

    if db_type is not None:
        # Создание новой базы с заданным типом
        cur.execute("DELETE FROM _meta WHERE key='db_type'")
        cur.execute("INSERT INTO _meta (key, value) VALUES ('db_type', ?)", (db_type,))
        if db_type == "invest":
            cur.execute("DELETE FROM _meta WHERE key='schema_version'")
            cur.execute("INSERT INTO _meta (key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        con.commit()
        if db_type == "invest":
            _create_mines_sections_schema(cur)
            _seed_mines(cur)
            _create_invest_schema(cur)
        elif db_type == "services":
            _create_mines_sections_schema(cur)
            _seed_mines(cur)
            _create_services_schema(cur)
        con.commit()
        con.close()
        return

    # Открытие существующей — миграция схемы до текущей версии
    if existing_type is None:
        cur.execute("INSERT INTO _meta (key, value) VALUES ('db_type', 'invest')")
        existing_type = "invest"
    if existing_type == "services":
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_contracts'")
        if cur.fetchone() is None:
            cur.execute("UPDATE _meta SET value='invest' WHERE key='db_type'")
            existing_type = "invest"
    if existing_type == "invest":
        _create_mines_sections_schema(cur)
        _seed_mines(cur)
        _create_invest_schema(cur)
        _run_migrations(con)
    elif existing_type == "services":
        _create_mines_sections_schema(cur)
        _seed_mines(cur)
        _create_services_schema(cur)
    con.commit()
    con.close()

def _create_mines_sections_schema(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mine_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY(mine_id) REFERENCES mines(id)
    )""")

def _seed_mines(cur):
    cur.execute("SELECT COUNT(*) FROM mines")
    if cur.fetchone()[0] > 0:
        return
    cur.execute("INSERT INTO mines (name) VALUES ('Жалпак'), ('Центральный Мынкудук')")

def _create_invest_schema(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        budget REAL NOT NULL DEFAULT 0,
        comment TEXT,
        created_at TEXT NOT NULL,
        out_of_budget INTEGER NOT NULL DEFAULT 0,
        mine_id INTEGER,
        section_id INTEGER,
        FOREIGN KEY(mine_id) REFERENCES mines(id),
        FOREIGN KEY(section_id) REFERENCES sections(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS corrections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        new_budget REAL NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        added_by TEXT DEFAULT '',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        file_path TEXT,
        note TEXT,
        added_by TEXT DEFAULT '',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contracts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        contractor TEXT,
        file_path TEXT,
        note TEXT,
        added_by TEXT DEFAULT '',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS revisions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_project_id INTEGER NOT NULL,
        target_project_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        added_by TEXT DEFAULT '',
        FOREIGN KEY(source_project_id) REFERENCES projects(id),
        FOREIGN KEY(target_project_id) REFERENCES projects(id)
    )""")

def _create_services_schema(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS service_contracts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contractor TEXT,
        total_amount REAL NOT NULL DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        mine_id INTEGER,
        section_id INTEGER,
        note TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(mine_id) REFERENCES mines(id),
        FOREIGN KEY(section_id) REFERENCES sections(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS service_acts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        period_start TEXT NOT NULL,
        period_end TEXT,
        act_date TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        FOREIGN KEY(contract_id) REFERENCES service_contracts(id)
    )""")

def seed_if_empty():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM projects")
    cnt = cur.fetchone()["c"]
    if cnt == 0:
        now = datetime.date.today().isoformat()
        demo = [
            ("Компрессорная станция", 20_000_000, "Исходный бюджет", now),
            ("ПНA МРПН", 15_000_000, "Исходный бюджет", now),
            ("Hilux для ГТП", 25_000_000, "Исходный бюджет", now),
        ]
        cur.executemany("INSERT INTO projects(name, budget, comment, created_at) VALUES(?,?,?,?)", demo)
        con.commit()
    con.close()

# -------- Справочники: рудники и участки (общие для invest и services)
def list_mines():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT id, name FROM mines ORDER BY name")
    rows = cur.fetchall()
    con.close()
    return [(r[0], r[1]) for r in rows]

def list_sections(mine_id: int | None = None):
    con = connect()
    cur = con.cursor()
    if mine_id is not None:
        cur.execute("SELECT id, mine_id, name FROM sections WHERE mine_id=? ORDER BY name", (mine_id,))
    else:
        cur.execute("SELECT id, mine_id, name FROM sections ORDER BY mine_id, name")
    rows = cur.fetchall()
    con.close()
    return [(r[0], r[1], r[2]) for r in rows]

def create_mine(name: str) -> int:
    con = connect()
    cur = con.cursor()
    cur.execute("INSERT INTO mines (name) VALUES (?)", (name.strip(),))
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid

def create_section(mine_id: int, name: str) -> int:
    con = connect()
    cur = con.cursor()
    cur.execute("INSERT INTO sections (mine_id, name) VALUES (?, ?)", (mine_id, name.strip()))
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid

def update_mine(mine_id: int, name: str):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE mines SET name=? WHERE id=?", (name.strip(), mine_id))
    con.commit()
    con.close()

def update_section(section_id: int, mine_id: int, name: str):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE sections SET mine_id=?, name=? WHERE id=?", (mine_id, name.strip(), section_id))
    con.commit()
    con.close()

def delete_section(section_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE projects SET section_id=NULL WHERE section_id=?", (section_id,))
    try:
        cur.execute("UPDATE service_contracts SET section_id=NULL WHERE section_id=?", (section_id,))
    except sqlite3.OperationalError:
        pass
    cur.execute("DELETE FROM sections WHERE id=?", (section_id,))
    con.commit()
    con.close()

def get_mine_name(mine_id: int | None) -> str:
    if mine_id is None:
        return ""
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT name FROM mines WHERE id=?", (mine_id,))
    r = cur.fetchone()
    con.close()
    return r[0] if r else ""

def get_section_name(section_id: int | None) -> str:
    if section_id is None:
        return ""
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT name FROM sections WHERE id=?", (section_id,))
    r = cur.fetchone()
    con.close()
    return r[0] if r else ""

def delete_mine(mine_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE projects SET mine_id=NULL, section_id=NULL WHERE mine_id=?", (mine_id,))
    try:
        cur.execute("UPDATE service_contracts SET mine_id=NULL, section_id=NULL WHERE mine_id=?", (mine_id,))
    except sqlite3.OperationalError:
        pass
    cur.execute("DELETE FROM sections WHERE mine_id=?", (mine_id,))
    cur.execute("DELETE FROM mines WHERE id=?", (mine_id,))
    con.commit()
    con.close()

# -------- Projects (invest)
def list_projects():
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, name, budget, comment, created_at, out_of_budget, mine_id, section_id
                   FROM projects ORDER BY id ASC""")
    rows = cur.fetchall()
    con.close()
    result = []
    for r in rows:
        ob = r[5] if len(r) > 5 else 0
        mid = r[6] if len(r) > 6 else None
        sid = r[7] if len(r) > 7 else None
        result.append((r[0], r[1], r[2], r[3], r[4], 1 if ob else 0, mid, sid))
    return result

def get_project(project_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, name, budget, comment, created_at, out_of_budget, mine_id, section_id
                   FROM projects WHERE id=?""", (project_id,))
    r = cur.fetchone()
    con.close()
    if not r:
        return None
    ob = r[5] if len(r) > 5 else 0
    return (r[0], r[1], r[2], r[3], r[4], 1 if ob else 0, r[6] if len(r) > 6 else None, r[7] if len(r) > 7 else None)

def create_project(name: str, budget: float, comment: str | None, out_of_budget: bool = False, mine_id: int | None = None, section_id: int | None = None):
    con = connect()
    cur = con.cursor()
    cur.execute("""INSERT INTO projects(name, budget, comment, created_at, out_of_budget, mine_id, section_id)
                   VALUES(?,?,?,?,?,?,?)""",
                (name, float(budget or 0), comment or "", datetime.date.today().isoformat(), 1 if out_of_budget else 0, mine_id, section_id))
    con.commit()
    con.close()

def update_project_mine_section(project_id: int, mine_id: int | None, section_id: int | None):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE projects SET mine_id=?, section_id=? WHERE id=?", (mine_id, section_id, project_id))
    con.commit()
    con.close()

def update_project_out_of_budget(project_id: int, out_of_budget: bool):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE projects SET out_of_budget=? WHERE id=?", (1 if out_of_budget else 0, project_id))
    con.commit()
    con.close()

# -------- Corrections
def record_correction(project_id: int, new_budget: float, date: str, note: str | None, added_by: str | None = None):
    con = connect()
    cur = con.cursor()
    who = (added_by or get_windows_user()) or ""
    cur.execute("INSERT INTO corrections(project_id, new_budget, date, note, added_by) VALUES(?,?,?,?,?)",
                (project_id, float(new_budget), date, note or "", who))
    cur.execute("UPDATE projects SET budget=? WHERE id=?", (float(new_budget), project_id))
    con.commit()
    con.close()

def get_correction(corr_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM corrections WHERE id=?", (corr_id,))
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def update_correction(corr_id: int, new_budget: float, date: str, note: str | None):
    con = connect()
    cur = con.cursor()
    # узнаем project_id, чтобы синхронизировать текущий base если это последний по дате
    cur.execute("SELECT project_id FROM corrections WHERE id=?", (corr_id,))
    row = cur.fetchone()
    if not row:
        con.close(); return
    project_id = row["project_id"]
    cur.execute("UPDATE corrections SET new_budget=?, date=?, note=? WHERE id=?",
                (float(new_budget), date, note or "", corr_id))
    # Будем считать корректировку «источником истины» — перезапишем текущий base
    cur.execute("UPDATE projects SET budget=? WHERE id=?", (float(new_budget), project_id))
    con.commit()
    con.close()

def delete_correction(corr_id: int):
    con = connect()
    cur = con.cursor()
    # удаляем запись; базовый бюджет проекта НЕ откатываем автоматически
    cur.execute("DELETE FROM corrections WHERE id=?", (corr_id,))
    con.commit()
    con.close()

# -------- Marketing
def record_marketing(project_id: int, amount: float, date: str, file_path: str | None, note: str | None = None, added_by: str | None = None):
    con = connect()
    cur = con.cursor()
    who = (added_by or get_windows_user()) or ""
    cur.execute("INSERT INTO marketing(project_id, amount, date, file_path, note, added_by) VALUES(?,?,?,?,?,?)",
                (project_id, float(amount), date, file_path, note or "", who))
    con.commit()
    con.close()

def get_marketing(mkt_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM marketing WHERE id=?", (mkt_id,))
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def get_last_marketing_for_project(project_id: int) -> dict | None:
    """Последняя запись маркетинга по проекту (по дате и id), для предзаполнения формы."""
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT id, amount, date, file_path, note FROM marketing WHERE project_id=? ORDER BY date DESC, id DESC LIMIT 1",
        (project_id,)
    )
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def update_marketing(mkt_id: int, amount: float, date: str, file_path: str | None, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE marketing SET amount=?, date=?, file_path=?, note=? WHERE id=?",
                (float(amount), date, file_path, note or "", mkt_id))
    con.commit()
    con.close()

def delete_marketing(mkt_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM marketing WHERE id=?", (mkt_id,))
    con.commit()
    con.close()

# -------- Contracts
def record_contract(project_id: int, amount: float, date: str, contractor: str | None, file_path: str | None, note: str | None = None, added_by: str | None = None):
    con = connect()
    cur = con.cursor()
    who = (added_by or get_windows_user()) or ""
    cur.execute("INSERT INTO contracts(project_id, amount, date, contractor, file_path, note, added_by) VALUES(?,?,?,?,?,?,?)",
                (project_id, float(amount), date, contractor, file_path, note or "", who))
    con.commit()
    con.close()

def get_contract(cnt_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM contracts WHERE id=?", (cnt_id,))
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def get_last_contract_for_project(project_id: int) -> dict | None:
    """Последняя запись договора по проекту (по дате и id), для предзаполнения формы."""
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT id, amount, date, contractor, file_path, note FROM contracts WHERE project_id=? ORDER BY date DESC, id DESC LIMIT 1",
        (project_id,)
    )
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def update_contract(cnt_id: int, amount: float, date: str, contractor: str | None, file_path: str | None, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE contracts SET amount=?, date=?, contractor=?, file_path=?, note=? WHERE id=?",
                (float(amount), date, contractor, file_path, note or "", cnt_id))
    con.commit()
    con.close()

def delete_contract(cnt_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM contracts WHERE id=?", (cnt_id,))
    con.commit()
    con.close()

# -------- Revisions
def record_revision(source_project_id: int, target_project_id: int, amount: float, date: str, note: str | None, added_by: str | None = None):
    if source_project_id == target_project_id:
        raise ValueError("Нельзя делать ревизию в ту же статью.")
    amt = float(amount)
    if amt <= 0:
        raise ValueError("Сумма должна быть больше нуля.")

    con = connect()
    try:
        cur = con.cursor()
        who = (added_by or get_windows_user()) or ""

        # считаем доступную сумму у источника (have)
        # have = base + rev_in - rev_out
        cur.execute("SELECT budget FROM projects WHERE id=?", (source_project_id,))
        r = cur.fetchone()
        base = float(r[0]) if r else 0.0

        cur.execute("SELECT COALESCE(SUM(amount),0) FROM revisions WHERE target_project_id=?", (source_project_id,))
        rev_in = float(cur.fetchone()[0] or 0.0)
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM revisions WHERE source_project_id=?", (source_project_id,))
        rev_out = float(cur.fetchone()[0] or 0.0)

        available = base + rev_in - rev_out

        # запрещаем перерасход
        EPS = 1e-6
        if amt - available > EPS:
            raise ValueError(f"Недостаточно средств в источнике. Доступно: {available:.2f}")

        # если хватает — проводим ревизию
        cur.execute("""
            INSERT INTO revisions(source_project_id, target_project_id, amount, date, note, added_by)
            VALUES(?,?,?,?,?,?)
        """, (source_project_id, target_project_id, amt, date, note or "", who))

        con.commit()
    finally:
        con.close()


def get_revision(rev_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM revisions WHERE id=?", (rev_id,))
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def update_revision(rev_id: int, amount: float, date: str, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE revisions SET amount=?, date=?, note=? WHERE id=?",
                (float(amount), date, note or "", rev_id))
    con.commit()
    con.close()

def delete_revision(rev_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM revisions WHERE id=?", (rev_id,))
    con.commit()
    con.close()

# -------- Aggregations
def _sum(cur, query, args):
    cur.execute(query, args)
    row = cur.fetchone()
    return float((row[0] if row else 0) or 0.0)

def compute_project_status(project_id: int) -> dict:
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT budget FROM projects WHERE id=?", (project_id,))
    r = cur.fetchone()
    base = float(r[0]) if r else 0.0

    rev_in = _sum(cur, "SELECT SUM(amount) FROM revisions WHERE target_project_id=?", (project_id,))
    rev_out = _sum(cur, "SELECT SUM(amount) FROM revisions WHERE source_project_id=?", (project_id,))

    have = base + rev_in - rev_out

    cur.execute("SELECT amount FROM contracts WHERE project_id=? ORDER BY date DESC, id DESC LIMIT 1", (project_id,))
    contract_row = cur.fetchone()

    cur.execute("SELECT amount FROM marketing WHERE project_id=? ORDER BY date DESC, id DESC LIMIT 1", (project_id,))
    marketing_row = cur.fetchone()

    contract_amount = float(contract_row[0]) if contract_row else None
    marketing_amount = float(marketing_row[0]) if marketing_row else None

    if contract_row:
        need = float(contract_row[0])
        stage = "contract"
    elif marketing_row:
        need = float(marketing_row[0])
        stage = "marketing"
    else:
        need = base
        stage = "none"

    diff = have - need
    con.close()
    return {"have": have, "need": need, "diff": diff, "stage": stage, "marketing_amount": marketing_amount, "contract_amount": contract_amount}

# -------- Timeline & last revision
def get_project_timeline(project_id: int) -> list[dict]:
    con = connect(); cur = con.cursor()
    rows = []

    # corrections
    cur.execute("SELECT id, date, new_budget, note, added_by FROM corrections WHERE project_id=?", (project_id,))
    for r in cur.fetchall():
        rows.append({"id": r["id"], "kind": "correction", "date": r["date"], "type": "Корректировка",
                     "amount": float(r["new_budget"]), "note": r["note"] or "", "file_path": None, "added_by": (r["added_by"] or "")})

    # marketing
    cur.execute("SELECT id, date, amount, note, file_path, added_by FROM marketing WHERE project_id=?", (project_id,))
    for r in cur.fetchall():
        rows.append({"id": r["id"], "kind": "marketing", "date": r["date"], "type": "Маркетинг",
                     "amount": float(r["amount"]), "note": r["note"] or "", "file_path": r["file_path"], "added_by": (r["added_by"] or "")})

    # contracts
    cur.execute("SELECT id, date, amount, note, file_path, contractor, added_by FROM contracts WHERE project_id=?", (project_id,))
    for r in cur.fetchall():
        t = "Договор" + (f" ({r['contractor']})" if r["contractor"] else "")
        rows.append({"id": r["id"], "kind": "contract", "date": r["date"], "type": t,
                     "amount": float(r["amount"]), "note": r["note"] or "", "file_path": r["file_path"], "added_by": (r["added_by"] or "")})

    # revisions in (+)
    cur.execute("SELECT id, date, amount, note, source_project_id, added_by FROM revisions WHERE target_project_id=?", (project_id,))
    for r in cur.fetchall():
        cur2 = con.cursor()
        cur2.execute("SELECT name FROM projects WHERE id=?", (r["source_project_id"],))
        src_name = cur2.fetchone()
        t = f"Ревизия (+) из «{(src_name['name'] if src_name else str(r['source_project_id']))}»"
        rows.append({"id": r["id"], "kind": "revision_in", "date": r["date"], "type": t,
                     "amount": float(r["amount"]), "note": r["note"] or "", "file_path": None, "sign": "+", "added_by": (r["added_by"] or "")})

    # revisions out (−)
    cur.execute("SELECT id, date, amount, note, target_project_id, added_by FROM revisions WHERE source_project_id=?", (project_id,))
    for r in cur.fetchall():
        cur2 = con.cursor()
        cur2.execute("SELECT name FROM projects WHERE id=?", (r["target_project_id"],))
        dst_name = cur2.fetchone()
        t = f"Ревизия (−) в «{(dst_name['name'] if dst_name else str(r['target_project_id']))}»"
        rows.append({"id": r["id"], "kind": "revision_out", "date": r["date"], "type": t,
                     "amount": float(r["amount"]), "note": r["note"] or "", "file_path": None, "sign": "-", "added_by": (r["added_by"] or "")})

    con.close()
    rows.sort(key=lambda x: (x["date"] or "", x["type"]))
    return rows

def get_last_revision_for_project(project_id: int) -> dict | None:
    con = connect(); cur = con.cursor()
    cur.execute("""
        SELECT id, source_project_id, target_project_id, amount, date, note
        FROM revisions
        WHERE source_project_id=? OR target_project_id=?
        ORDER BY date DESC, id DESC LIMIT 1
    """, (project_id, project_id))
    r = cur.fetchone(); con.close()
    if not r: return None
    return {"id": r["id"], "source_project_id": r["source_project_id"], "target_project_id": r["target_project_id"],
            "amount": float(r["amount"]), "date": r["date"], "note": r["note"]}

def get_project_activity_counts(project_id: int) -> dict:
    """Сколько событий связано со статьёй (для запрета удаления)."""
    con = connect(); cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM corrections WHERE project_id=?", (project_id,))
    corr = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM marketing WHERE project_id=?", (project_id,))
    mkt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contracts WHERE project_id=?", (project_id,))
    ctr = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM revisions WHERE source_project_id=? OR target_project_id=?", (project_id, project_id))
    rev = cur.fetchone()[0]
    con.close()
    return {"corrections": corr, "marketing": mkt, "contracts": ctr, "revisions": rev}

def can_delete_project(project_id: int) -> bool:
    c = get_project_activity_counts(project_id)
    return (c["corrections"] + c["marketing"] + c["contracts"] + c["revisions"]) == 0

def update_project_name(project_id: int, new_name: str):
    con = connect(); cur = con.cursor()
    cur.execute("UPDATE projects SET name=? WHERE id=?", (new_name.strip(), project_id))
    con.commit(); con.close()

def delete_project(project_id: int):
    """Удаляет статью, ЕСЛИ по ней не было действий; иначе бросает ValueError."""
    if not can_delete_project(project_id):
        counts = get_project_activity_counts(project_id)
        raise ValueError(
            "Нельзя удалить: по статье есть история.\n"
            f"Корректировок: {counts['corrections']}, "
            f"Маркетингов: {counts['marketing']}, "
            f"Договоров: {counts['contracts']}, "
            f"Ревизий: {counts['revisions']}."
        )
    con = connect(); cur = con.cursor()
    cur.execute("DELETE FROM projects WHERE id=?", (project_id,))
    con.commit(); con.close()

# -------- Услуги и работы (service_contracts + service_acts)
def list_service_contracts():
    """Список договоров: id, name, contractor, total_amount, start_date, end_date, mine_id, section_id, note, created_at."""
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, name, contractor, total_amount, start_date, end_date, mine_id, section_id, note, created_at
                   FROM service_contracts ORDER BY id ASC""")
    rows = cur.fetchall()
    con.close()
    return [tuple(r) for r in rows]

def get_service_contract(contract_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, name, contractor, total_amount, start_date, end_date, mine_id, section_id, note, created_at
                   FROM service_contracts WHERE id=?""", (contract_id,))
    r = cur.fetchone()
    con.close()
    return dict(r) if r else None

def create_service_contract(name: str, contractor: str | None, total_amount: float, start_date: str | None, end_date: str | None, mine_id: int | None, section_id: int | None, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("""INSERT INTO service_contracts (name, contractor, total_amount, start_date, end_date, mine_id, section_id, note, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (name.strip(), contractor or "", float(total_amount or 0), start_date or "", end_date or "", mine_id, section_id, note or "", datetime.date.today().isoformat()))
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid

def update_service_contract(cid: int, name: str, contractor: str | None, total_amount: float, start_date: str | None, end_date: str | None, mine_id: int | None, section_id: int | None, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("""UPDATE service_contracts SET name=?, contractor=?, total_amount=?, start_date=?, end_date=?, mine_id=?, section_id=?, note=?
                   WHERE id=?""",
                (name.strip(), contractor or "", float(total_amount or 0), start_date or "", end_date or "", mine_id, section_id, note or "", cid))
    con.commit()
    con.close()

def delete_service_contract(contract_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM service_acts WHERE contract_id=?", (contract_id,))
    cur.execute("DELETE FROM service_contracts WHERE id=?", (contract_id,))
    con.commit()
    con.close()

def get_service_contract_totals(contract_id: int) -> dict:
    """Списано всего и остаток по договору."""
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT total_amount FROM service_contracts WHERE id=?", (contract_id,))
    r = cur.fetchone()
    total = float(r[0]) if r else 0.0
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM service_acts WHERE contract_id=?", (contract_id,))
    spent = float(cur.fetchone()[0] or 0)
    con.close()
    return {"total": total, "spent": spent, "remaining": total - spent}

def list_service_acts(contract_id: int) -> list[dict]:
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, contract_id, period_start, period_end, act_date, amount, note
                   FROM service_acts WHERE contract_id=? ORDER BY act_date, id""", (contract_id,))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]

def get_service_act(act_id: int) -> dict | None:
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT id, contract_id, period_start, period_end, act_date, amount, note
                   FROM service_acts WHERE id=?""", (act_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None

def add_service_act(contract_id: int, period_start: str, period_end: str | None, act_date: str, amount: float, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("""INSERT INTO service_acts (contract_id, period_start, period_end, act_date, amount, note)
                   VALUES(?,?,?,?,?,?)""",
                (contract_id, period_start, period_end or "", act_date, float(amount), note or ""))
    con.commit()
    con.close()

def update_service_act(act_id: int, period_start: str, period_end: str | None, act_date: str, amount: float, note: str | None):
    con = connect()
    cur = con.cursor()
    cur.execute("""UPDATE service_acts SET period_start=?, period_end=?, act_date=?, amount=?, note=? WHERE id=?""",
                (period_start, period_end or "", act_date, float(amount), note or "", act_id))
    con.commit()
    con.close()

def delete_service_act(act_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM service_acts WHERE id=?", (act_id,))
    con.commit()
    con.close()
