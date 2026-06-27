"""Accounting — 个人记账软件入口。

启动流程:
1. 初始化 SQLite 数据库（首次运行自动建表 + 预设数据）
2. (阶段 4) 启动 PyQt6 主窗口
"""

import sys
from db.schema import init_db
from db.connection import db_exists


def main():
    """应用入口。"""
    # 1. 数据库初始化
    init_db()

    # 2. Core 层服务就绪（阶段 2 完成）
    # from core.transaction import add_transaction, list_transactions, ...
    # from core.statistics import StatisticsService, ...
    # from core.budget import BudgetService, ...
    # from core.reminder import ReminderService, ...
    # from core.template import TemplateService, ...
    # from core.export import ExportService, ...
    # from core.backup import BackupService, ...

    print("=" * 50)
    print("Accounting — 个人记账软件")
    print("=" * 50)
    print(f"数据库: {'已就绪' if db_exists() else '初始化失败'}")
    print("Core 层: 7 个服务模块已就绪 (阶段 2)")
    print("GUI 层: 将在阶段 4 实现")
    print("=" * 50)


if __name__ == "__main__":
    main()
