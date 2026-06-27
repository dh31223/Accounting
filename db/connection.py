"""SQLite 数据库连接管理模块。

提供连接获取、关闭、上下文管理器，以及行工厂配置。
"""

import sqlite3
import os
from pathlib import Path

# 数据库文件路径：项目根目录下的 accounting.db
DB_DIR = Path(__file__).resolve().parent.parent
DB_PATH = DB_DIR / "accounting.db"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接。

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 使查询结果可通过列名访问
    conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式提升并发性能
    conn.execute("PRAGMA foreign_keys=ON")    # 启用外键约束
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """关闭数据库连接。

    Args:
        conn: 要关闭的连接对象
    """
    if conn is not None:
        conn.close()


class DatabaseContext:
    """数据库连接上下文管理器。

    用法:
        with DatabaseContext() as conn:
            conn.execute("SELECT ...")
    """

    def __enter__(self) -> sqlite3.Connection:
        self.conn = get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        close_connection(self.conn)
        return False  # 不吞掉异常


def db_exists() -> bool:
    """检查数据库文件是否已存在。"""
    return DB_PATH.exists()
