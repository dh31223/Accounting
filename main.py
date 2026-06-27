"""Accounting — 个人记账软件入口。

启动流程:
1. 初始化 SQLite 数据库（首次运行自动建表 + 预设数据）
2. 启动 PyQt6 主窗口
"""

import sys
import os

# ---- 必须在 QApplication 创建之前设置 ----
# Linux 中文输入法支持：
# PyQt6(pip) 自带 Qt 6.11，与系统 fcitx 插件(Qt 6.4) ABI 不兼容。
# 改用 ibus 协议 — PyQt6 自带 libibusplatforminputcontextplugin.so。
if "QT_IM_MODULE" not in os.environ:
    os.environ["QT_IM_MODULE"] = "ibus"

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
