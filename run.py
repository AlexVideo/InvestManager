# Лаунчер: запуск app.py через .venv без полного пути (обходит проблему кириллицы в пути при Run из Cursor)
import os
import subprocess
import sys

base = os.path.dirname(os.path.abspath(__file__))
os.chdir(base)
venv_python = os.path.join(base, ".venv", "Scripts", "python.exe")
app_py = os.path.join(base, "app.py")

if not os.path.isfile(venv_python):
    print("Не найден:", venv_python)
    print("Запустите из терминала: .\\.venv\\Scripts\\python.exe app.py")
    sys.exit(1)

sys.exit(subprocess.run([venv_python, app_py], cwd=base).returncode)
