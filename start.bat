@echo off
title AI Harness
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo            AI Harness - iFlow Auto Development
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

iflow --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] iFlow CLI not found
    echo Run: npm install -g @iflow-ai/iflow-cli
    echo.
)

python "%~dp0iflow_runner.py" --interactive

echo.
pause