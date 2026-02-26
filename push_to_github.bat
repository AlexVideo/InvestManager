@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "REMOTE=https://github.com/AlexVideo/InvestManager.git"

echo [1/5] Проверка Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo Установите Git: https://git-scm.com/
    pause
    exit /b 1
)

echo [2/5] Инициализация (если ещё не репозиторий)...
if not exist .git git init

echo Настройка имени и email для коммитов (только в этом репозитории)...
git config user.email "videoalex.korday@gmail.com"
git config user.name "Alex"

echo [3/5] Добавление файлов и коммит...
git add .
git status -s
set "VER=0.0.0"
for /f "delims=" %%v in ('python -c "import version; print(version.APP_VERSION)" 2^>nul') do set "VER=%%v"
if "%VER%"=="" for /f "delims=" %%v in ('".venv\Scripts\python.exe" -c "import version; print(version.APP_VERSION)" 2^>nul') do set "VER=%%v"
git commit -m "Invest Manager %VER%" 2>nul || git commit -m "Обновление проекта"
git branch -M main 2>nul

echo Создание тега v%VER% (для отката к версии: git checkout v%VER%)...
git tag -a "v%VER%" -m "Release %VER%" 2>nul

echo [4/5] Подключение удалённого репозитория...
git remote remove origin 2>nul
git remote add origin "%REMOTE%"

echo [5/5] Синхронизация с GitHub и отправка...
echo.
echo Сначала подтянем изменения с GitHub (если репозиторий уже что-то содержал)...
git pull origin main --allow-unrelated-histories --no-edit 2>nul
if errorlevel 1 (
    echo Конфликтов нет или pull не нужен. Отправляем...
) else (
    echo Подтянуто. Отправляем...
)
echo.
echo Сейчас может быть запрос логина и пароля.
echo Логин: videoalex.korday@gmail.com
echo Пароль: используйте токен (GitHub ^> Settings ^> Developer settings ^> Personal access tokens), не пароль от почты!
echo.
git push -u origin main
if errorlevel 1 (
    echo.
    echo Если push не прошёл — выполните вручную: git push -u origin main
    echo И введите логин и токен при запросе.
    pause
    exit /b 1
)

echo.
echo Отправка тегов (чтобы на GitHub можно было откатиться к версии)...
git push origin --tags

echo.
echo Готово. Откат к предыдущей версии: git checkout v0.5.1
echo Или на GitHub: Code ^> вкладка веток ^> Tags ^> выбрать версию.
pause
