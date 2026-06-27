"""账单提醒模块。

管理定期账单提醒，支持到期检测和重复周期。
"""

from datetime import date, timedelta
from calendar import monthrange
from typing import Optional

from db.connection import get_connection, close_connection
from core.models import BillReminder


class ReminderService:
    """账单提醒服务。"""

    # ---- CRUD ----

    @staticmethod
    def create(reminder: BillReminder, conn=None) -> BillReminder:
        """创建账单提醒。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            """INSERT INTO bill_reminders (name, amount, due_date, repeat_cycle, note)
               VALUES (?, ?, ?, ?, ?)""",
            (reminder.name, reminder.amount, reminder.due_date,
             reminder.repeat_cycle, reminder.note)
        )

        if own_conn:
            conn.commit()

        reminder.id = cursor.lastrowid
        return reminder

    @staticmethod
    def get_all(conn=None) -> list[BillReminder]:
        """获取所有提醒，按到期日排序。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            "SELECT * FROM bill_reminders ORDER BY due_date"
        ).fetchall()

        if own_conn:
            close_connection(conn)

        return [BillReminder.from_row(r) for r in rows]

    @staticmethod
    def update(reminder: BillReminder, conn=None) -> bool:
        """更新提醒。"""
        if reminder.id is None:
            raise ValueError("更新操作需要 reminder.id")

        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            """UPDATE bill_reminders
               SET name=?, amount=?, due_date=?, repeat_cycle=?, note=?
               WHERE id=?""",
            (reminder.name, reminder.amount, reminder.due_date,
             reminder.repeat_cycle, reminder.note, reminder.id)
        )

        if own_conn:
            conn.commit()
            close_connection(conn)

        return cursor.rowcount > 0

    @staticmethod
    def delete(reminder_id: int, conn=None) -> bool:
        """删除提醒。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        cursor = conn.execute(
            "DELETE FROM bill_reminders WHERE id = ?", (reminder_id,)
        )

        if own_conn:
            conn.commit()
            close_connection(conn)

        return cursor.rowcount > 0

    # ---- 到期检测 ----

    @staticmethod
    def get_due_soon(days_ahead: int = 7, conn=None) -> list[BillReminder]:
        """获取未来 N 天内到期的提醒。

        自动处理重复周期：如果设置了 monthly/yearly 且当前到期日已过，
        自动推进到下个周期。
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        today = date.today()
        deadline = today + timedelta(days=days_ahead)

        rows = conn.execute(
            "SELECT * FROM bill_reminders WHERE due_date <= ? ORDER BY due_date",
            (deadline.isoformat(),)
        ).fetchall()

        if own_conn:
            close_connection(conn)

        result = []
        for row in rows:
            reminder = BillReminder.from_row(row)
            due = date.fromisoformat(reminder.due_date)

            # 如果已过期且有重复周期，推进日期
            while due < today:
                if reminder.repeat_cycle == "monthly":
                    # 移到下个月同一天
                    if due.month == 12:
                        due = due.replace(year=due.year + 1, month=1)
                    else:
                        due = due.replace(month=due.month + 1)
                elif reminder.repeat_cycle == "yearly":
                    due = due.replace(year=due.year + 1)
                else:
                    break  # 不重复则保留原日期

            if due <= deadline:
                reminder.due_date = due.isoformat()
                result.append(reminder)

        return result

    @staticmethod
    def get_overdue(conn=None) -> list[BillReminder]:
        """获取已过期的提醒。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        today = date.today().isoformat()
        rows = conn.execute(
            "SELECT * FROM bill_reminders WHERE due_date < ? AND repeat_cycle = 'none' ORDER BY due_date",
            (today,)
        ).fetchall()

        if own_conn:
            close_connection(conn)

        return [BillReminder.from_row(r) for r in rows]


# 便捷函数
def add_reminder(name: str, due_date: str, amount: float = None,
                 repeat_cycle: str = "none", note: str = "") -> BillReminder:
    return ReminderService.create(BillReminder(
        name=name, due_date=due_date, amount=amount,
        repeat_cycle=repeat_cycle, note=note
    ))


def get_due_reminders(days_ahead: int = 7) -> list[BillReminder]:
    return ReminderService.get_due_soon(days_ahead)
