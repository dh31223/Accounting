"""数据模型模块。

使用 dataclass 定义核心数据结构，与 SQLite 表一一对应。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Transaction:
    """交易记录模型。"""
    date: str          # 'YYYY-MM-DD'
    type: str          # 'income' | 'expense'
    amount: float
    category: str
    attribute: str     # 'worthy' | 'joy' | 'necessity' | 'waste'
    note: str = ""
    account: str = "银行卡"
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转为字典（用于 SQL 插入）。"""
        d = asdict(self)
        # 移除 None 值的主键/时间戳字段
        d.pop("id", None)
        d.pop("created_at", None)
        d.pop("updated_at", None)
        return d

    @staticmethod
    def from_row(row) -> "Transaction":
        """从 sqlite3.Row 构造。"""
        return Transaction(
            id=row["id"],
            date=row["date"],
            type=row["type"],
            amount=row["amount"],
            category=row["category"],
            attribute=row["attribute"],
            note=row["note"] or "",
            account=row["account"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class Budget:
    """预算模型。category 为 None 表示总预算。"""
    amount: float
    period_month: str      # 'YYYY-MM'
    category: Optional[str] = None
    id: Optional[int] = None

    @staticmethod
    def from_row(row) -> "Budget":
        """从 sqlite3.Row 构造。"""
        return Budget(
            id=row["id"],
            category=row["category"],
            amount=row["amount"],
            period_month=row["period_month"],
        )


@dataclass
class BillReminder:
    """账单提醒模型。"""
    name: str
    due_date: str          # 'YYYY-MM-DD'
    amount: Optional[float] = None
    repeat_cycle: str = "none"   # 'none' | 'monthly' | 'yearly'
    note: str = ""
    id: Optional[int] = None

    @staticmethod
    def from_row(row) -> "BillReminder":
        """从 sqlite3.Row 构造。"""
        return BillReminder(
            id=row["id"],
            name=row["name"],
            amount=row["amount"],
            due_date=row["due_date"],
            repeat_cycle=row["repeat_cycle"] or "none",
            note=row["note"] or "",
        )


@dataclass
class Template:
    """交易模板模型。"""
    name: str
    type: str              # 'income' | 'expense'
    amount: float
    category: str
    attribute: str
    account: str = "银行卡"
    note: str = ""
    id: Optional[int] = None

    @staticmethod
    def from_row(row) -> "Template":
        """从 sqlite3.Row 构造。"""
        return Template(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            amount=row["amount"],
            category=row["category"],
            attribute=row["attribute"],
            account=row["account"],
            note=row["note"] or "",
        )
