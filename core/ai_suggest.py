"""AI 预算建议模块。

- 本地聚合近 3 个月收支数据生成文本摘要
- 调用 DeepSeek API（OpenAI 兼容格式）获取预算建议
- 每次仅发送几百 tokens，成本极低
"""

import os
import json
from datetime import date, timedelta

import httpx

from core.statistics import StatisticsService
from core.budget import BudgetService

DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

DEFAULT_SYSTEM_PROMPT = """你是一位专业的个人理财顾问。用户会提供近几个月的收支数据摘要。
请分析后给出：

1. **整体评估**：收支平衡状况、储蓄率是否健康
2. **分类建议**：指出超支分类，给出合理的月度预算数字
3. **优化方向**：2-3 条可执行的省钱建议
4. **预算模板**：以表格形式给出下个月各分类的建议预算金额

请用中文回复，简洁务实，不要泛泛而谈。格式使用 Markdown。"""


def _aggregate_data(months: int = 3) -> dict:
    """聚合近 N 个月数据为文本摘要。"""
    today = date.today()
    end = today.isoformat()
    start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    # 往前推 months 个月
    for _ in range(months - 1):
        start = (start.replace(day=1) - timedelta(days=1)).replace(day=1)
    start = start.isoformat()

    # 汇总
    summary = StatisticsService.summary_by_period(start, end)

    # 月度数据
    monthly = StatisticsService.monthly_summary(start, end)

    # 支出分类占比
    cat_breakdown = StatisticsService.category_breakdown(start, end, "expense")

    # 属性分布
    attr_breakdown = StatisticsService.attribute_breakdown(start, end)

    # 当前预算
    period = f"{today.year}-{today.month:02d}"
    budgets = BudgetService.get_budgets(period)
    budget_map = {b.category: b.amount for b in budgets}

    return {
        "start": start,
        "end": end,
        "total_income": summary["total_income"],
        "total_expense": summary["total_expense"],
        "balance": summary["balance"],
        "transaction_count": summary["transaction_count"],
        "monthly": monthly,
        "category_breakdown": cat_breakdown,
        "attribute_breakdown": attr_breakdown,
        "current_budgets": budget_map,
        "period": period,
    }


def _build_user_message(data: dict) -> str:
    """根据聚合数据构建用户消息。"""
    parts = []
    parts.append(f"数据范围：{data['start']} 至 {data['end']}")
    parts.append(f"总收入：¥{data['total_income']:,.2f}")
    parts.append(f"总支出：¥{data['total_expense']:,.2f}")
    parts.append(f"结余：¥{data['balance']:,.2f}")
    parts.append(f"交易笔数：{data['transaction_count']}")
    parts.append(f"储蓄率：{data['balance']/data['total_income']*100:.1f}%" if data["total_income"] > 0 else "储蓄率：N/A")

    # 月度趋势
    parts.append("\n月度收支趋势：")
    for m in data["monthly"]:
        parts.append(f"  {m['month']}: 收入 ¥{m['income']:,.2f} | 支出 ¥{m['expense']:,.2f}")

    # 分类占比
    parts.append("\n支出分类占比：")
    for c in data["category_breakdown"]:
        parts.append(f"  {c['category']}: ¥{c['amount']:,.2f} ({c['percentage']}%)")

    # 属性分布
    parts.append("\n消费属性分布：")
    for a in data["attribute_breakdown"]:
        parts.append(f"  {a['label']}: ¥{a['amount']:,.2f} ({a['percentage']}%)")

    # 当前预算
    if data["current_budgets"]:
        parts.append("\n当前月度预算：")
        for cat, amt in data["current_budgets"].items():
            label = "总预算" if cat is None else cat
            parts.append(f"  {label}: ¥{amt:,.2f}")

    return "\n".join(parts)


async def get_budget_suggestions(
    api_key: str,
    system_prompt: str = None,
    months: int = 3,
) -> str:
    """获取 AI 预算建议。

    Args:
        api_key: DeepSeek API Key
        system_prompt: 自定义系统提示词（可选）
        months: 聚合近几个月数据

    Returns:
        AI 生成的预算建议文本（Markdown 格式）
    """
    if not api_key:
        raise ValueError("请先设置 DeepSeek API Key")

    # 1. 聚合本地数据
    data = _aggregate_data(months)

    # 2. 构建消息
    user_msg = _build_user_message(data)

    # 3. 调用 API
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            DEEPSEEK_API,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
                "stream": False,
            },
        )

        if resp.status_code != 200:
            error_detail = resp.text
            try:
                err = resp.json()
                error_detail = err.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"API 请求失败 ({resp.status_code}): {error_detail}")

        result = resp.json()
        return result["choices"][0]["message"]["content"]


def get_suggestions_sync(
    api_key: str,
    system_prompt: str = None,
    months: int = 3,
) -> str:
    """同步版本：获取 AI 预算建议（供 PyQt 调用）。"""
    import asyncio
    return asyncio.run(get_budget_suggestions(api_key, system_prompt, months))
