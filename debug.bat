@echo off
title AI Harness Debug
echo ============================================================
echo            AI Harness - Debug Mode
echo ============================================================
echo.

echo [DEBUG] Current directory: %cd%
echo [DEBUG] Script directory: %~dp0
echo.

echo [DEBUG] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo.

echo [DEBUG] Checking iflow_runner.py exists...
if not exist "%~dp0iflow_runner.py" (
    echo [ERROR] iflow_runner.py not found in %~dp0
    pause
    exit /b 1
)
echo [OK] iflow_runner.py found
echo.

echo [DEBUG] Running Python script...
echo.
python "%~dp0iflow_runner.py" --interactive

echo.
echo [DEBUG] Script finished. Exit code: %errorlevel%
echo.
pause
