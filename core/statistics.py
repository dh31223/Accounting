"""统计分析引擎模块。

提供日/周/月/年维度的收支汇总、分类/属性占比、趋势分析。
"""

from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
import calendar

from db.connection import get_connection, close_connection


class StatisticsService:
    """统计分析服务。"""

    @staticmethod
    def summary_by_period(
        start_date: str,
        end_date: str,
        conn=None,
    ) -> dict:
        """获取指定时间段内的收支汇总。

        Returns:
            {
                'total_income': float,
                'total_expense': float,
                'balance': float,
                'transaction_count': int,
            }
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT type, SUM(amount) as total, COUNT(*) as cnt
               FROM transactions
               WHERE date BETWEEN ? AND ?
               GROUP BY type""",
            (start_date, end_date)
        ).fetchall()

        total_income = 0.0
        total_expense = 0.0
        count = 0
        for r in rows:
            count += r["cnt"]
            if r["type"] == "income":
                total_income = r["total"] or 0.0
            else:
                total_expense = r["total"] or 0.0

        if own_conn:
            close_connection(conn)

        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "balance": round(total_income - total_expense, 2),
            "transaction_count": count,
        }

    @staticmethod
    def daily_summary(
        start_date: str,
        end_date: str,
        conn=None,
    ) -> list[dict]:
        """每日收支明细。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT date, type, SUM(amount) as total
               FROM transactions
               WHERE date BETWEEN ? AND ?
               GROUP BY date, type
               ORDER BY date""",
            (start_date, end_date)
        ).fetchall()

        # 合并同一天的收支
        daily = defaultdict(lambda: {"date": "", "income": 0.0, "expense": 0.0})
        for r in rows:
            daily[r["date"]]["date"] = r["date"]
            if r["type"] == "income":
                daily[r["date"]]["income"] = round(r["total"], 2)
            else:
                daily[r["date"]]["expense"] = round(r["total"], 2)

        # 填充没有交易的日子
        result = []
        cursor = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        while cursor <= end:
            key = cursor.isoformat()
            if key in daily:
                result.append(daily[key])
            else:
                result.append({"date": key, "income": 0.0, "expense": 0.0})
            cursor += timedelta(days=1)

        if own_conn:
            close_connection(conn)

        return result

    @staticmethod
    def weekly_summary(
        start_date: str,
        end_date: str,
        conn=None,
    ) -> list[dict]:
        """按周汇总（ISO week）。"""
        daily = StatisticsService.daily_summary(start_date, end_date, conn)
        weeks = defaultdict(lambda: {"week": "", "income": 0.0, "expense": 0.0})

        for d in daily:
            dt = date.fromisoformat(d["date"])
            iso_year, iso_week, _ = dt.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            # 用周的起始日作为标签
            week_start = dt - timedelta(days=dt.weekday())
            weeks[key]["week"] = week_start.isoformat()
            weeks[key]["income"] += d["income"]
            weeks[key]["expense"] += d["expense"]

        result = sorted(weeks.values(), key=lambda w: w["week"])
        for w in result:
            w["income"] = round(w["income"], 2)
            w["expense"] = round(w["expense"], 2)
        return result

    @staticmethod
    def monthly_summary(
        start_date: str,
        end_date: str,
        conn=None,
    ) -> list[dict]:
        """按月汇总。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT strftime('%Y-%m', date) as month, type, SUM(amount) as total
               FROM transactions
               WHERE date BETWEEN ? AND ?
               GROUP BY month, type
               ORDER BY month""",
            (start_date, end_date)
        ).fetchall()

        monthly = defaultdict(lambda: {"month": "", "income": 0.0, "expense": 0.0})
        for r in rows:
            monthly[r["month"]]["month"] = r["month"]
            if r["type"] == "income":
                monthly[r["month"]]["income"] = round(r["total"], 2)
            else:
                monthly[r["month"]]["expense"] = round(r["total"], 2)

        if own_conn:
            close_connection(conn)

        return sorted(monthly.values(), key=lambda m: m["month"])

    @staticmethod
    def yearly_summary(conn=None) -> list[dict]:
        """按年汇总。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT strftime('%Y', date) as year, type, SUM(amount) as total
               FROM transactions
               GROUP BY year, type
               ORDER BY year"""
        ).fetchall()

        yearly = defaultdict(lambda: {"year": "", "income": 0.0, "expense": 0.0})
        for r in rows:
            yearly[r["year"]]["year"] = r["year"]
            if r["type"] == "income":
                yearly[r["year"]]["income"] = round(r["total"], 2)
            else:
                yearly[r["year"]]["expense"] = round(r["total"], 2)

        if own_conn:
            close_connection(conn)

        return sorted(yearly.values(), key=lambda y: y["year"])

    @staticmethod
    def category_breakdown(
        start_date: str,
        end_date: str,
        txn_type: str = "expense",
        conn=None,
    ) -> list[dict]:
        """按分类统计占比。

        Returns:
            [{'category': '餐饮', 'amount': 2800.0, 'percentage': 33.0}, ...]
        """
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT category, SUM(amount) as total
               FROM transactions
               WHERE type = ? AND date BETWEEN ? AND ?
               GROUP BY category
               ORDER BY total DESC""",
            (txn_type, start_date, end_date)
        ).fetchall()

        total = sum(r["total"] for r in rows)
        result = []
        for r in rows:
            pct = round((r["total"] / total) * 100, 1) if total > 0 else 0.0
            result.append({
                "category": r["category"],
                "amount": round(r["total"], 2),
                "percentage": pct,
            })

        if own_conn:
            close_connection(conn)

        return result

    @staticmethod
    def attribute_breakdown(
        start_date: str,
        end_date: str,
        conn=None,
    ) -> list[dict]:
        """按属性统计占比。"""
        own_conn = conn is None
        if own_conn:
            conn = get_connection()

        rows = conn.execute(
            """SELECT attribute, SUM(amount) as total, COUNT(*) as cnt
               FROM transactions
               WHERE date BETWEEN ? AND ?
               GROUP BY attribute
               ORDER BY total DESC""",
            (start_date, end_date)
        ).fetchall()

        total = sum(r["total"] for r in rows)
        attr_labels = {
            "worthy": "💚 值得",
            "joy": "💛 悦己",
            "necessity": "📋 刚需",
            "waste": "🚫 浪费",
        }
        result = []
        for r in rows:
            pct = round((r["total"] / total) * 100, 1) if total > 0 else 0.0
            result.append({
                "attribute": r["attribute"],
                "label": attr_labels.get(r["attribute"], r["attribute"]),
                "amount": round(r["total"], 2),
                "count": r["cnt"],
                "percentage": pct,
            })

        if own_conn:
            close_connection(conn)

        return result

    @staticmethod
    def spending_trend(
        start_date: str,
        end_date: str,
        granularity: str = "monthly",
        conn=None,
    ) -> list[dict]:
        """消费趋势数据 — 供折线图使用。

        Args:
            granularity: 'daily' | 'weekly' | 'monthly'
        """
        if granularity == "daily":
            daily = StatisticsService.daily_summary(start_date, end_date, conn)
            return [{"label": d["date"], "expense": d["expense"], "income": d["income"]} for d in daily]
        elif granularity == "weekly":
            weekly = StatisticsService.weekly_summary(start_date, end_date, conn)
            return [{"label": w["week"], "expense": w["expense"], "income": w["income"]} for w in weekly]
        else:
            monthly = StatisticsService.monthly_summary(start_date, end_date, conn)
            return [{"label": m["month"], "expense": m["expense"], "income": m["income"]} for m in monthly]


# ============================================================
# 当前月份的便捷日期
# ============================================================

def current_month_range() -> tuple[str, str]:
    """返回当前月份的起始和结束日期。"""
    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    return first_day.isoformat(), last_day.isoformat()


def current_week_range() -> tuple[str, str]:
    """返回本周的起止日期（周一到周日）。"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()
