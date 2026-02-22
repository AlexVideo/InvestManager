# build_exe.py - Скрипт для сборки exe
import os
import subprocess
import sys

# Переходим в директорию скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))

print(f"Текущая директория: {os.getcwd()}")
print(f"Директория скрипта: {script_dir}")
print(f"Spec файл существует: {os.path.exists(os.path.join(script_dir, 'InvestManager.spec'))}")

# Запускаем PyInstaller с указанием рабочего каталога
cmd = [sys.executable, "-m", "PyInstaller", "InvestManager.spec", "--clean", "--noconfirm"]
print(f"Запускаем: {' '.join(cmd)}")
print(f"В директории: {script_dir}")
result = subprocess.run(cmd, cwd=script_dir, check=False)

sys.exit(result.returncode)

