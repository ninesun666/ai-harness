@echo off
chcp 65001 >nul 2>&1
title AI Harness

echo.
echo ============================================================
echo            AI Harness - iFlow Auto Development
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.8+
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
