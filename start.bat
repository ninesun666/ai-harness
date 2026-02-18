@echo off
chcp 65001 >nul
title AI Harness - 自动化开发工具

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║           AI Harness - iFlow 自动化开发工具               ║
echo ╠══════════════════════════════════════════════════════════╣
echo ║  让 AI 自主完成软件开发任务                                ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查 iFlow
iflow --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 iFlow CLI，部分功能可能不可用
    echo 请运行: npm install -g @iflow-ai/iflow-cli
    echo.
)

:: 运行主程序
python "%~dp0iflow_runner.py" --interactive

pause
