"""交易模板模块。

管理常用交易模板，支持一键生成交易记录。
"""

from typing import Optional

from db.connection import get_connection, close_connection
from core.models import Template, Transaction
from core.transaction import TransactionService


class TemplateService:
    """交易模板服务。"""

    # ---- CRUD ----

    @staticmethod
    def create(tmpl: Template, conn=None) -> Template:
        """创建模板。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            """INSERT INTO templates (name, type, amount, category, attribute, account, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tmpl.name, tmpl.type, tmpl.amount, tmpl.category,
             tmpl.attribute, tmpl.account, tmpl.note)
        )

        if own_conn:
            conn.commit()

        tmpl.id = cursor.lastrowid
        return tmpl

    @staticmethod
    def get_all(conn=None) -> list[Template]:
        """获取所有模板。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            "SELECT * FROM templates ORDER BY type, name"
        ).fetchall()

        if own_conn:
            close_connection(conn)

        return [Template.from_row(r) for r in rows]

    @staticmethod
    def update(tmpl: Template, conn=None) -> bool:
        """更新模板。"""
        if tmpl.id is None:
            raise ValueError("更新操作需要 tmpl.id")

        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            """UPDATE templates
               SET name=?, type=?, amount=?, category=?, attribute=?, account=?, note=?
               WHERE id=?""",
            (tmpl.name, tmpl.type, tmpl.amount, tmpl.category,
             tmpl.attribute, tmpl.account, tmpl.note, tmpl.id)
        )

        if own_conn:
            conn.commit()
            close_connection(conn)

        return cursor.rowcount > 0

    @staticmethod
    def delete(tmpl_id: int, conn=None) -> bool:
        """删除模板。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            "DELETE FROM templates WHERE id = ?", (tmpl_id,)
        )

        if own_conn:
            conn.commit()
            close_connection(conn)

        return cursor.rowcount > 0

    # ---- 一键生成交易 ----

    @staticmethod
    def apply_template(tmpl_id: int, date_str: str, conn=None) -> Optional[Transaction]:
        """使用模板创建一条交易记录。

        Args:
            tmpl_id: 模板 ID
            date_str: 交易日期 'YYYY-MM-DD'

        Returns:
            创建的交易记录，模板不存在返回 None
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        row = conn.execute(
            "SELECT * FROM templates WHERE id = ?", (tmpl_id,)
        ).fetchone()

        if not row:
            if own_conn:
                close_connection(conn)
            return None

        tmpl = Template.from_row(row)
        txn = Transaction(
            date=date_str,
            type=tmpl.type,
            amount=tmpl.amount,
            category=tmpl.category,
            attribute=tmpl.attribute,
            note=tmpl.note,
            account=tmpl.account,
        )

        result = TransactionService.create(txn, conn)

        if own_conn:
            conn.commit()
            close_connection(conn)

        return result
