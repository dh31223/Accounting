"""Accounting — 个人记账软件入口。

启动流程:
1. 初始化 SQLite 数据库（首次运行自动建表 + 预设数据）
2. 启动 PyQt6 主窗口

支持平台: Linux / Windows / macOS
"""

import sys
import os
from pathlib import Path

# ---- 平台检测 ----
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"

# ---- 必须在 QApplication 创建之前设置 ----
if IS_LINUX and "QT_IM_MODULE" not in os.environ:
    # Linux: 使用系统 PyQt6 (Qt 6.4) + fcitx Qt6 插件，ABI 一致。
    os.environ["QT_IM_MODULE"] = "fcitx"

# Windows PyInstaller 打包后资源路径辅助
def get_app_dir() -> Path:
    """获取应用根目录（兼容 PyInstaller 打包）。"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，sys.executable 是 exe 路径
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from db.schema import init_db
from db.connection import db_exists
from ui.main_window import MainWindow


def main():
    """应用入口。"""
    # 1. 数据库初始化
    init_db()

    # 2. 启动 GUI
    app = QApplication(sys.argv)
    app.setApplicationName("Accounting")
    app.setApplicationDisplayName("Accounting — 个人记账")

    # 高 DPI 缩放支持
    app.setStyle("Fusion")

    # 禁用高分屏自动缩放（PyQt6 默认启用以避免模糊）
    # 保留默认设置

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
