@echo off
title DOOM AI — Setup
cd /d "%~dp0"

echo.
echo === DOOM AI Setup ===
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Install Python 3.10+ from python.org and check "Add to PATH".
    pause
    exit /b 1
)

echo Installing dependencies...
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist .env (
    echo Creating .env from example...
    copy .env.example .env >nul
)

cd ..
echo.
echo Setup complete.
echo Now run: start-doom.bat
echo.
pause
