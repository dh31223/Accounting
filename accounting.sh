#!/bin/bash
# Accounting — 个人记账软件 启动脚本
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# 确保 fcitx 输入法可用
export QT_IM_MODULE=fcitx

# 启动应用
exec uv run python main.py
