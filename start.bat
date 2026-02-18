@echo off
title AI Harness
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo            AI Harness - iFlow Auto Development
echo ============================================================
echo.

python "%~dp0iflow_runner.py" --interactive

echo.
echo Press any key to exit...
pause >nul
