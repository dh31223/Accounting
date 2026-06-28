#!/bin/bash
# Accounting — 个人记账软件 启动脚本
# 自动检测脚本所在目录，移动到任何位置都不影响启动
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# 确保 fcitx 输入法可用
export QT_IM_MODULE=fcitx

# 直接用 venv 中的 Python 启动（避免依赖桌面环境的 PATH）
exec "$APP_DIR/.venv/bin/python3" "$APP_DIR/main.py"
