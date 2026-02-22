@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Завершение слияния и отправка на GitHub...
git add .gitignore README.md
git commit -m "Merge: разрешены конфликты, сохранена версия проекта"
git push -u origin main

if errorlevel 1 (
    echo.
    echo Если push снова запросит логин/пароль — введите токен вместо пароля.
)
pause
