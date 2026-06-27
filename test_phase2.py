"""阶段 2 业务逻辑测试脚本。

测试所有 core 层服务：Transaction, Statistics, Budget, Reminder, Template, Export, Backup。
"""

import sys
from datetime import date, timedelta

from core.models import Transaction, Budget, BillReminder, Template
from core.transaction import TransactionService as TxSvc
from core.statistics import StatisticsService as StatSvc, current_month_range
from core.budget import BudgetService as BudSvc
from core.reminder import ReminderService as RemSvc
from core.template import TemplateService as TplSvc
from core.export import ExportService as ExpSvc
from core.backup import BackupService as BkpSvc


def test_transaction_crud():
    """测试交易增删改查。"""
    print("\n=== 1. 交易 CRUD 测试 ===")

    # CREATE
    txn = Transaction(
        date="2025-06-25", type="expense", amount=35.5,
        category="餐饮", attribute="necessity", note="午饭外卖",
        account="支付宝"
    )
    result = TxSvc.create(txn)
    assert result.id is not None, "CREATE 失败"
    print(f"  ✅ CREATE: id={result.id}, amount={result.amount}")

    # CREATE income
    txn2 = TxSvc.create(Transaction(
        date="2025-06-26", type="income", amount=5000.0,
        category="工资", attribute="worthy", note="六月工资",
        account="银行卡"
    ))
    print(f"  ✅ CREATE income: id={txn2.id}")

    # READ by ID
    fetched = TxSvc.get_by_id(result.id)
    assert fetched is not None and fetched.amount == 35.5, "READ by ID 失败"
    print(f"  ✅ READ: {fetched.category} {fetched.amount}元")

    # READ list with filters
    all_txns = TxSvc.list_all()
    assert len(all_txns) >= 2, "列表查询失败"
    print(f"  ✅ LIST 全部: {len(all_txns)} 条")

    by_type = TxSvc.list_all(txn_type="income")
    assert len(by_type) >= 1, "按类型筛选失败"
    print(f"  ✅ LIST 收入: {len(by_type)} 条")

    by_date = TxSvc.list_all(date_from="2025-06-01", date_to="2025-06-30")
    assert len(by_date) >= 2, "按日期筛选失败"
    print(f"  ✅ LIST 6月: {len(by_date)} 条")

    # UPDATE
    result.amount = 42.0
    result.note = "午饭外卖 + 饮料"
    updated = TxSvc.update(result)
    assert updated, "UPDATE 失败"
    refreshed = TxSvc.get_by_id(result.id)
    assert refreshed.amount == 42.0, "更新后金额不匹配"
    print(f"  ✅ UPDATE: {result.amount}元, note={result.note}")

    # DELETE
    deleted = TxSvc.delete(result.id)
    assert deleted, "DELETE 失败"
    assert TxSvc.get_by_id(result.id) is None, "删除后仍能查到"
    print(f"  ✅ DELETE: id={result.id} 已删除")

    # 清理
    TxSvc.delete(txn2.id)


def test_statistics():
    """测试统计分析。"""
    print("\n=== 2. 统计分析测试 ===")

    # 插入测试数据
    today = date.today()
    data = [
        ("expense", 35.0, "餐饮", "necessity"),
        ("expense", 200.0, "购物", "joy"),
        ("expense", 150.0, "交通", "necessity"),
        ("expense", 50.0, "娱乐", "worthy"),
        ("expense", 20.0, "医疗", "necessity"),
        ("income", 8000.0, "工资", "worthy"),
        ("income", 500.0, "收红包", "joy"),
    ]

    ids = []
    for i, (typ, amt, cat, attr) in enumerate(data):
        txn = TxSvc.create(Transaction(
            date=(today - timedelta(days=i)).isoformat(),
            type=typ, amount=amt, category=cat, attribute=attr,
            account="银行卡"
        ))
        ids.append(txn.id)

    start, end = current_month_range()

    # 汇总
    summary = StatSvc.summary_by_period(start, end)
    assert summary["transaction_count"] >= 7, "交易数统计错误"
    print(f"  ✅ 本月汇总: 收入{summary['total_income']}, 支出{summary['total_expense']}, 结余{summary['balance']}")

    # 分类统计
    breakdown = StatSvc.category_breakdown(start, end, "expense")
    assert len(breakdown) >= 4, "分类统计错误"
    print(f"  ✅ 支出分类: {[(b['category'], b['amount']) for b in breakdown[:3]]}")

    # 属性统计
    attr_bd = StatSvc.attribute_breakdown(start, end)
    assert len(attr_bd) >= 3, "属性统计错误"
    print(f"  ✅ 属性占比: {[(a['label'], a['percentage']) for a in attr_bd[:3]]}")

    # 趋势
    trend = StatSvc.spending_trend(start, end, "monthly")
    assert len(trend) >= 1, "趋势数据错误"
    print(f"  ✅ 月度趋势: {len(trend)} 个月")

    # 清理
    for i in ids:
        TxSvc.delete(i)


def test_budget():
    """测试预算管理。"""
    print("\n=== 3. 预算测试 ===")

    month = date.today().strftime("%Y-%m")

    # 设定总预算
    total = BudSvc.set_budget(None, 3000.0, month)
    assert total.id is not None, "总预算设置失败"
    print(f"  ✅ 总预算: {total.amount} 元")

    # 设定分项预算
    cat = BudSvc.set_budget("餐饮", 1000.0, month)
    assert cat.amount == 1000.0, "分项预算设置失败"
    print(f"  ✅ 分项预算: {cat.category}={cat.amount}")

    # 获取预算
    budgets = BudSvc.get_budgets(month)
    assert len(budgets) == 2, "获取预算数量错误"
    print(f"  ✅ 获取预算: {len(budgets)} 条")

    # 进度
    progress = BudSvc.get_budget_progress(month)
    print(f"  ✅ 预算进度: 总花费{progress['total_spent']}, 进度{progress['total_pct']}%")

    # 超支检查
    overspent = BudSvc.check_overspend(month)
    print(f"  ✅ 超支检查: {len(overspent)} 项超支")

    # 清理
    from db.connection import get_connection, close_connection
    conn = get_connection()
    conn.execute("DELETE FROM budgets")
    conn.commit()
    close_connection(conn)


def test_reminder():
    """测试账单提醒。"""
    print("\n=== 4. 账单提醒测试 ===")

    today = date.today()

    # CREATE
    r = RemSvc.create(BillReminder(
        name="房租", amount=3000.0,
        due_date=today.replace(day=5).isoformat(),
        repeat_cycle="monthly", note="每月5号"
    ))
    assert r.id is not None, "提醒 CREATE 失败"
    print(f"  ✅ CREATE: {r.name} ({r.due_date})")

    r2 = RemSvc.create(BillReminder(
        name="信用卡", amount=None,
        due_date=(today + timedelta(days=3)).isoformat(),
        repeat_cycle="none", note=""
    ))
    print(f"  ✅ CREATE: {r2.name}")

    # READ
    all_rem = RemSvc.get_all()
    assert len(all_rem) >= 2, "获取提醒列表失败"
    print(f"  ✅ GET ALL: {len(all_rem)} 条")

    # 到期检测
    due = RemSvc.get_due_soon(days_ahead=7)
    print(f"  ✅ 即将到期: {len(due)} 条 — {[(d.name, d.due_date) for d in due]}")

    # UPDATE
    r.note = "每月5号付房租"
    RemSvc.update(r)
    updated = RemSvc.get_all()
    assert updated[0].note == "每月5号付房租", "更新失败"
    print(f"  ✅ UPDATE: note={updated[0].note}")

    # DELETE
    RemSvc.delete(r.id)
    RemSvc.delete(r2.id)
    print(f"  ✅ DELETE: 已清理")


def test_template():
    """测试交易模板。"""
    print("\n=== 5. 交易模板测试 ===")

    # CREATE
    t = TplSvc.create(Template(
        name="☕ 美式咖啡", type="expense", amount=18.0,
        category="餐饮", attribute="necessity",
        account="支付宝", note="公司楼下咖啡"
    ))
    assert t.id is not None, "模板 CREATE 失败"
    print(f"  ✅ CREATE: {t.name} {t.amount}元")

    # 一键生成交易
    today = date.today().isoformat()
    txn = TplSvc.apply_template(t.id, today)
    assert txn is not None and txn.amount == 18.0, "模板生成交易失败"
    print(f"  ✅ 一键生成: date={txn.date}, amount={txn.amount}")

    # 清理
    TplSvc.delete(t.id)
    TxSvc.delete(txn.id)
    print(f"  ✅ DELETE: 已清理模板和交易")


def test_export():
    """测试 Excel 导出。"""
    print("\n=== 6. Excel 导出测试 ===")

    # 先创建一些测试数据
    today = date.today()
    ids = []
    for i in range(5):
        txn = TxSvc.create(Transaction(
            date=(today - timedelta(days=i)).isoformat(),
            type="expense" if i % 2 == 0 else "income",
            amount=10.0 * (i + 1),
            category="餐饮" if i % 2 == 0 else "工资",
            attribute="necessity" if i % 2 == 0 else "worthy",
            account="支付宝" if i % 2 == 0 else "银行卡",
            note=f"测试记录{i}"
        ))
        ids.append(txn.id)

    filepath = str(txn.__class__.__module__)  # dummy
    import tempfile, os
    tmpfile = os.path.join(tempfile.gettempdir(), "test_export.xlsx")
    count = ExpSvc.export_transactions(tmpfile)
    assert count >= 5, "导出数量错误"
    assert os.path.exists(tmpfile), "导出文件未生成"
    size = os.path.getsize(tmpfile)
    os.remove(tmpfile)
    print(f"  ✅ 导出: {count} 条记录, 文件大小 {size} bytes")

    # 清理
    for i in ids:
        TxSvc.delete(i)


def test_backup():
    """测试备份与还原。"""
    print("\n=== 7. 备份还原测试 ===")
    path = BkpSvc.backup()
    import os
    assert os.path.exists(path), "备份文件未生成"
    size = os.path.getsize(path)
    print(f"  ✅ 备份: {path} ({size} bytes)")

    backups = BkpSvc.list_backups()
    assert len(backups) >= 1, "备份列表为空"
    print(f"  ✅ 备份列表: {len(backups)} 个文件")

    # 恢复测试（从刚创建的备份）
    restored = BkpSvc.restore(path)
    assert restored, "还原失败"
    print(f"  ✅ 还原成功")

    # 清理
    os.remove(path)
    print(f"  ✅ 清理完成")


if __name__ == "__main__":
    print("=" * 50)
    print("阶段 2 业务逻辑单元测试")
    print("=" * 50)

    try:
        test_transaction_crud()
        test_statistics()
        test_budget()
        test_reminder()
        test_template()
        test_export()
        test_backup()

        print("\n" + "=" * 50)
        print("🎉 全部测试通过！")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
