@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "JUNCTION=C:\IM"
set "TARGET=%~dp0"
if "%TARGET:~-1%"=="\" set "TARGET=%TARGET:~0,-1%"

echo Creating junction: %JUNCTION% -^> "%TARGET%"
echo.

if exist "%JUNCTION%" (
    echo Removing existing %JUNCTION%...
    rmdir "%JUNCTION%"
)

mkdir "%JUNCTION%" 2>nul
if exist "%JUNCTION%" (
    rmdir "%JUNCTION%"
)

mklink /J "%JUNCTION%" "%TARGET%"
if errorlevel 1 (
    echo.
    echo Failed. Try running this script as Administrator: right-click -^> Run as administrator
    echo Or run in Administrator CMD: mklink /J C:\IM "%TARGET%"
    pause
    exit /b 1
)

echo.
echo Done. In Cursor: File -^> Open Folder -^> choose C:\IM
echo Then Run (F5 or Play) will work. Your project files are the same.
pause
