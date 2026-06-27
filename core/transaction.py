"""交易 CRUD 服务模块。

提供交易的增删改查，支持多维度筛选。
"""

from datetime import date
from typing import Optional

from db.connection import get_connection, close_connection
from core.models import Transaction


class TransactionService:
    """交易记录服务。

    所有方法均为静态方法，可传入外部连接或内部管理连接。
    """

    # ---- CREATE ----

    @staticmethod
    def create(txn: Transaction, conn=None) -> Transaction:
        """创建一条交易记录。

        Args:
            txn: 交易对象（不需要 id，会自动生成）
            conn: 可选的外部数据库连接

        Returns:
            带 id 的完整 Transaction
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        try:
            cursor = conn.execute(
                """INSERT INTO transactions (date, type, amount, category, attribute, note, account)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (txn.date, txn.type, txn.amount, txn.category,
                 txn.attribute, txn.note, txn.account)
            )
            if own_conn:
                conn.commit()

            txn.id = cursor.lastrowid
            return txn
        except Exception:
            if own_conn:
                conn.rollback()
            raise
        finally:
            if own_conn:
                close_connection(conn)

    # ---- READ ----

    @staticmethod
    def get_by_id(txn_id: int, conn=None) -> Optional[Transaction]:
        """根据 ID 查询交易。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()

        if own_conn:
            close_connection(conn)

        return Transaction.from_row(row) if row else None

    @staticmethod
    def list_all(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        txn_type: Optional[str] = None,
        category: Optional[str] = None,
        attribute: Optional[str] = None,
        account: Optional[str] = None,
        order_by: str = "date DESC",
        limit: int = 500,
        offset: int = 0,
        conn=None,
    ) -> list[Transaction]:
        """查询交易列表，支持多维度筛选。

        Args:
            date_from: 起始日期 'YYYY-MM-DD'
            date_to: 结束日期 'YYYY-MM-DD'
            txn_type: 'income' | 'expense'
            category: 分类名
            attribute: 'worthy' | 'joy' | 'necessity' | 'waste'
            account: 账户名
            order_by: 排序字段
            limit: 最大返回条数
            offset: 偏移量

        Returns:
            符合条件的交易列表
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if txn_type:
            query += " AND type = ?"
            params.append(txn_type)
        if category:
            query += " AND category = ?"
            params.append(category)
        if attribute:
            query += " AND attribute = ?"
            params.append(attribute)
        if account:
            query += " AND account = ?"
            params.append(account)

        query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        if own_conn:
            close_connection(conn)

        return [Transaction.from_row(r) for r in rows]

    @staticmethod
    def count(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        txn_type: Optional[str] = None,
        category: Optional[str] = None,
        conn=None,
    ) -> int:
        """统计符合条件的交易条数。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
        params = []
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if txn_type:
            query += " AND type = ?"
            params.append(txn_type)
        if category:
            query += " AND category = ?"
            params.append(category)

        count = conn.execute(query, params).fetchone()[0]

        if own_conn:
            close_connection(conn)

        return count

    # ---- UPDATE ----

    @staticmethod
    def update(txn: Transaction, conn=None) -> bool:
        """更新一条交易记录（通过 txn.id 定位）。

        Returns:
            True 如果更新成功，False 如果记录不存在
        """
        if txn.id is None:
            raise ValueError("更新操作需要 txn.id")

        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        try:
            cursor = conn.execute(
                """UPDATE transactions
                   SET date=?, type=?, amount=?, category=?, attribute=?,
                       note=?, account=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (txn.date, txn.type, txn.amount, txn.category,
                 txn.attribute, txn.note, txn.account, txn.id)
            )

            if own_conn:
                conn.commit()

            return cursor.rowcount > 0
        except Exception:
            if own_conn:
                conn.rollback()
            raise
        finally:
            if own_conn:
                close_connection(conn)

    # ---- DELETE ----

    @staticmethod
    def delete(txn_id: int, conn=None) -> bool:
        """删除一条交易记录。

        Returns:
            True 如果删除成功
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        try:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE id = ?", (txn_id,)
            )

            if own_conn:
                conn.commit()

            return cursor.rowcount > 0
        except Exception:
            if own_conn:
                conn.rollback()
            raise
        finally:
            if own_conn:
                close_connection(conn)


# ============================================================
# 便捷函数：直接暴露顶级 API
# ============================================================

def add_transaction(date: str, txn_type: str, amount: float,
                    category: str, attribute: str = "necessity",
                    note: str = "", account: str = "银行卡") -> Transaction:
    """快捷创建交易。"""
    txn = Transaction(
        date=date, type=txn_type, amount=amount,
        category=category, attribute=attribute,
        note=note, account=account
    )
    return TransactionService.create(txn)


def get_transaction(txn_id: int) -> Optional[Transaction]:
    """快捷查询单条交易。"""
    return TransactionService.get_by_id(txn_id)


def list_transactions(**kwargs) -> list[Transaction]:
    """快捷查询交易列表。"""
    return TransactionService.list_all(**kwargs)


def update_transaction(txn: Transaction) -> bool:
    """快捷更新交易。"""
    return TransactionService.update(txn)


def delete_transaction(txn_id: int) -> bool:
    """快捷删除交易。"""
    return TransactionService.delete(txn_id)
