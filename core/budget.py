"""预算管理模块。

支持总预算和分项预算的设定、查询、超支检测。
"""

from typing import Optional

from db.connection import get_connection, close_connection
from core.models import Budget


class BudgetService:
    """预算管理服务。"""

    @staticmethod
    def set_budget(category: Optional[str], amount: float,
                   period_month: str, conn=None) -> Budget:
        """设定或更新预算。已存在同 category + period_month 则更新，否则插入。

        Args:
            category: None 表示总预算
            amount: 预算金额
            period_month: 'YYYY-MM'
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        existing = conn.execute(
            "SELECT id FROM budgets WHERE category IS ? AND period_month = ?",
            (category, period_month)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE budgets SET amount = ? WHERE id = ?",
                (amount, existing["id"])
            )
            budget_id = existing["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO budgets (category, amount, period_month) VALUES (?, ?, ?)",
                (category, amount, period_month)
            )
            budget_id = cursor.lastrowid

        if own_conn:
            conn.commit()
            close_connection(conn)

        return Budget(id=budget_id, category=category, amount=amount,
                      period_month=period_month)

    @staticmethod
    def get_budgets(period_month: str, conn=None) -> list[Budget]:
        """获取指定月份的所有预算。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            "SELECT * FROM budgets WHERE period_month = ?",
            (period_month,)
        ).fetchall()

        if own_conn:
            close_connection(conn)

        return [Budget.from_row(r) for r in rows]

    @staticmethod
    def get_total_budget(period_month: str, conn=None) -> Optional[Budget]:
        """获取指定月份的总预算。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        row = conn.execute(
            "SELECT * FROM budgets WHERE category IS NULL AND period_month = ?",
            (period_month,)
        ).fetchone()

        if own_conn:
            close_connection(conn)

        return Budget.from_row(row) if row else None

    @staticmethod
    def check_overspend(period_month: str, conn=None) -> list[dict]:
        """检查指定月份的超支情况。

        Returns:
            [{'category': '餐饮', 'budget': 3000, 'spent': 3500, 'overspent': 500, 'pct': 116.7}, ...]
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        budgets = {b.category: b.amount for b in
                   BudgetService.get_budgets(period_month, conn)}

        # 查询每个分类的实际支出
        rows = conn.execute(
            """SELECT category, SUM(amount) as spent
               FROM transactions
               WHERE type = 'expense'
                 AND strftime('%Y-%m', date) = ?
               GROUP BY category""",
            (period_month,)
        ).fetchall()

        results = []
        for r in rows:
            cat = r["category"]
            spent = r["spent"] or 0.0

            # 检查分类预算
            budget = budgets.get(cat)
            if budget and spent > budget:
                results.append({
                    "category": cat,
                    "budget": budget,
                    "spent": round(spent, 2),
                    "overspent": round(spent - budget, 2),
                    "pct": round(spent / budget * 100, 1),
                })

        # 检查总预算
        total_budget = budgets.get(None)
        if total_budget:
            total_spent = sum(r["spent"] or 0.0 for r in rows)
            if total_spent > total_budget:
                results.insert(0, {
                    "category": "总计",
                    "budget": total_budget,
                    "spent": round(total_spent, 2),
                    "overspent": round(total_spent - total_budget, 2),
                    "pct": round(total_spent / total_budget * 100, 1),
                })

        if own_conn:
            close_connection(conn)

        return results

    @staticmethod
    def get_budget_progress(period_month: str, conn=None) -> dict:
        """获取预算进度数据（用于进度条）。

        Returns:
            {'total_budget': float, 'total_spent': float, 'pct': float,
             'categories': [{'name': '餐饮', 'budget': 3000, 'spent': 2100, 'pct': 70.0}, ...]}
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        budgets = BudgetService.get_budgets(period_month, conn)
        budget_map = {b.category: b.amount for b in budgets}

        rows = conn.execute(
            """SELECT category, SUM(amount) as spent
               FROM transactions
               WHERE type = 'expense'
                 AND strftime('%Y-%m', date) = ?
               GROUP BY category""",
            (period_month,)
        ).fetchall()

        cat_progress = []
        total_spent = 0.0
        for r in rows:
            cat = r["category"]
            spent = r["spent"] or 0.0
            total_spent += spent
            budget = budget_map.get(cat)
            if budget:
                cat_progress.append({
                    "name": cat,
                    "budget": budget,
                    "spent": round(spent, 2),
                    "pct": round(spent / budget * 100, 1),
                })

        total_budget = budget_map.get(None, 0.0)

        if own_conn:
            close_connection(conn)

        return {
            "total_budget": total_budget,
            "total_spent": round(total_spent, 2),
            "total_pct": round(total_spent / total_budget * 100, 1) if total_budget else 0.0,
            "categories": cat_progress,
        }


# ============================================================
# 便捷函数
# ============================================================

def set_budget(category: Optional[str], amount: float, period_month: str) -> Budget:
    return BudgetService.set_budget(category, amount, period_month)


def check_overspend(period_month: str) -> list[dict]:
    return BudgetService.check_overspend(period_month)
