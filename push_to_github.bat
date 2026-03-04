@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "REMOTE=https://github.com/AlexVideo/InvestManager.git"

echo [1/5] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo Install Git: https://git-scm.com/
    pause
    exit /b 1
)

echo [2/5] Init repo if needed...
if not exist .git git init

echo Setting user and email for this repo...
git config user.email "videoalex.korday@gmail.com"
git config user.name "Alex"

echo [3/5] Add files and commit...
git add .
git status -s
set "VER=0.0.0"
for /f "delims=" %%v in ('python -c "import version; print(version.APP_VERSION)" 2^>nul') do set "VER=%%v"
if "%VER%"=="" for /f "delims=" %%v in ('".venv\Scripts\python.exe" -c "import version; print(version.APP_VERSION)" 2^>nul') do set "VER=%%v"
git commit -m "Invest Manager %VER%" 2>nul || git commit -m "Update"
git branch -M main 2>nul

echo Creating tag v%VER%...
git tag -a "v%VER%" -m "Release %VER%" 2>nul

echo [4/5] Adding remote origin...
git remote remove origin 2>nul
git remote add origin "%REMOTE%"

echo [5/5] Sync with GitHub...
echo.
echo Pulling from GitHub...
git pull origin main --allow-unrelated-histories --no-edit 2>nul
if errorlevel 1 (
    echo No pull needed. Pushing...
) else (
    echo Pull done. Pushing...
)
echo.
echo Login: videoalex.korday@gmail.com
echo Password: use Personal Access Token from GitHub - Settings - Developer settings - Personal access tokens
echo.
git push -u origin main
if errorlevel 1 (
    echo.
    echo If push failed, run: git push -u origin main
    echo Use your GitHub token as password.
    pause
    exit /b 1
)

echo.
echo Pushing tags...
git push origin --tags

echo.
echo Done. To checkout old version: git checkout v0.5.1
echo On GitHub: Code - Branches - Tags - pick version.
pause
