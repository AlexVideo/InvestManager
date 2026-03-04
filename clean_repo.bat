@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Удаление из репозитория всего, что теперь в .gitignore...
echo (Файлы на диске не трогаем — они просто перестанут отслеживаться Git.)
echo.

git rm -r --cached . 2>nul
git add .

echo.
git status

echo.
echo Выше: "deleted" = файл убран из репозитория (остаётся на диске).
echo.
git commit -m "Убрать из репозитория личные и служебные файлы (.gitignore)"
if errorlevel 1 (
    echo Коммит не создан — возможно, нечего коммитить или ошибка.
) else (
    echo Коммит создан. Отправляю на GitHub...
    git push
)
echo.
pause
