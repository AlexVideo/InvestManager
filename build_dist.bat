@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"

:: Short path (8.3) so PyInstaller and cmd get paths without spaces/Unicode
for %%I in ("%ROOT:~0,-1%") do set "S=%%~sI\"
if not defined S set "S=%ROOT%"

cd /d "%S%"
set "PYEXE=%S%.venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo Building to dist...
call "%PYEXE%" -m PyInstaller --noconfirm InvestManager.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed. Run: "%PYEXE%" -m pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo Done: dist\InvestManager\InvestManager.exe and dist\InvestManager\_internal\
echo Zip the folder dist\InvestManager manually if needed.
pause
