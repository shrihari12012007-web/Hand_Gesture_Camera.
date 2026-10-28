@echo off
title Hand Gesture Camera - Web Server
cd /d "%~dp0"

echo ==========================================================
echo Starting Hand Gesture Camera Web Server...
echo Opening http://localhost:5000 in your browser...
echo ==========================================================

start "" "http://localhost:5000"

if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" app.py
) else (
    python app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Web server stopped with error code %ERRORLEVEL%.
    pause
)
