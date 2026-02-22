@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"

for %%I in ("%ROOT:~0,-1%") do set "S=%%~sI\"
if not defined S set "S=%ROOT%"

cd /d "%S%"
set "PYEXE=%S%.venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

for /f "delims=" %%v in ('"%PYEXE%" -c "import version; print(version.APP_VERSION)"') do set "VER=%%v"
if not defined VER set "VER=0.0.0"

echo [1/3] PyInstaller...
call "%PYEXE%" -m PyInstaller --noconfirm InvestManager.spec
if errorlevel 1 (
    echo ERROR. Install: "%PYEXE%" -m pip install pyinstaller
    pause
    exit /b 1
)
echo Done: dist\InvestManager
echo.

set "SEVENZ="
if exist "C:\Program Files\7-Zip\7z.exe" set "SEVENZ=C:\Program Files\7-Zip\7z.exe"
if exist "C:\Program Files (x86)\7-Zip\7z.exe" set "SEVENZ=C:\Program Files (x86)\7-Zip\7z.exe"
if "%SEVENZ%"=="" (
    echo [2/3] 7-Zip not found. Install from https://www.7-zip.org/
    echo Use build_dist.bat to get only dist\InvestManager folder.
    pause
    exit /b 0
)

echo [2/3] Creating archive...
"%SEVENZ%" a -t7z -mx=5 "%S%dist\InvestManager.7z" "%S%dist\InvestManager\*"
if errorlevel 1 (
    echo ERROR creating archive.
    pause
    exit /b 1
)

echo [3/3] Building SFX...
set "SFX="
if exist "C:\Program Files\7-Zip\7z.sfx" set "SFX=C:\Program Files\7-Zip\7z.sfx"
if exist "C:\Program Files (x86)\7-Zip\7z.sfx" set "SFX=C:\Program Files (x86)\7-Zip\7z.sfx"
if "%SFX%"=="" (
    echo 7z.sfx not found.
    pause
    exit /b 1
)

copy /b "%SFX%" + "%S%sfx_config.txt" + "%S%dist\InvestManager.7z" "%S%dist\InvestManager_%VER%_setup.exe" >nul
if errorlevel 1 (
    echo ERROR creating SFX.
    pause
    exit /b 1
)

del "%S%dist\InvestManager.7z"
echo.
echo Done: dist\InvestManager_%VER%_setup.exe
pause
