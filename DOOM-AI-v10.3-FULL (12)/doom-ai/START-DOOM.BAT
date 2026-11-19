@echo off
title DOOM AI — Running
cd /d "%~dp0backend"

if not exist .env (
    echo .env missing. Run setup-doom.bat first.
    pause
    exit /b 1
)

echo.
echo Starting DOOM AI on http://localhost:8000
echo Press Ctrl+C to stop.
echo.

python main.py

echo.
pause
