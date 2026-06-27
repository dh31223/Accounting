"""Accounting — 个人记账软件入口。

启动流程:
1. 初始化 SQLite 数据库（首次运行自动建表 + 预设数据）
2. 启动 PyQt6 主窗口
"""

import sys
from db.schema import init_db


def main():
    """应用入口。"""
    # 1. 数据库初始化
    init_db()

    # 2. 启动 GUI（阶段 4 实现）
    print("数据库就绪。GUI 将在阶段 4 实现。")
    print("当前可用的模块: db/connection.py, db/schema.py")


if __name__ == "__main__":
    main()
