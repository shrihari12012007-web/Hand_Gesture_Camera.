@echo off
title Hand Gesture Camera - Desktop Controller
cd /d "%~dp0"

echo ==========================================================
echo Starting Hand Gesture Camera Desktop Controller...
echo ==========================================================

if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" desktop_controller.py
) else (
    python desktop_controller.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Hand Gesture Camera stopped with error code %ERRORLEVEL%.
    pause
)
