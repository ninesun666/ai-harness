#!/bin/bash
# AI Harness - 启动脚本 (Linux/macOS)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           AI Harness - iFlow 自动化开发工具               ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  让 AI 自主完成软件开发任务                                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查 iFlow
if ! command -v iflow &> /dev/null; then
    echo "[警告] 未找到 iFlow CLI，部分功能可能不可用"
    echo "请运行: npm install -g @iflow-ai/iflow-cli"
    echo ""
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 运行主程序
python3 "$SCRIPT_DIR/iflow_runner.py" --interactive
