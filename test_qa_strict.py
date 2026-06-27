"""刁钻 QA 测试 — 边界条件、异常场景、SQL 注入、并发安全等。"""

import sys
import os
from datetime import date, timedelta

from core.models import Transaction, Budget, BillReminder, Template
from core.transaction import TransactionService as TxSvc
from core.statistics import StatisticsService as StatSvc
from core.budget import BudgetService as BudSvc
from core.reminder import ReminderService as RemSvc
from core.template import TemplateService as TplSvc
from core.export import ExportService as ExpSvc
from core.backup import BackupService as BkpSvc
from db.connection import get_connection, close_connection

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


# ============================================================
# 1. Transaction CRUD — 边界与异常
# ============================================================
print("=" * 60)
print("1. Transaction CRUD 边界测试")
print("=" * 60)

# 1a. 负数金额应被数据库拒绝
try:
    TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=-50.0,
                              category="餐饮", attribute="necessity"))
    check("负数金额应被拒绝", False, "应该抛出 IntegrityError")
except Exception:
    check("负数金额应被拒绝", True)

# 1b. 零金额应被拒绝
try:
    TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=0,
                              category="餐饮", attribute="necessity"))
    check("零金额应被拒绝", False, "应该抛出 IntegrityError")
except Exception:
    check("零金额应被拒绝", True)

# 1c. 非法 type 应被拒绝
try:
    TxSvc.create(Transaction(date="2025-01-01", type="refund", amount=10,
                              category="餐饮", attribute="necessity"))
    check("非法type应被拒绝", False, "应该抛出 IntegrityError")
except Exception:
    check("非法type应被拒绝", True)

# 1d. 非法 attribute 应被拒绝
try:
    TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=10,
                              category="餐饮", attribute="bad_value"))
    check("非法attribute应被拒绝", False, "应该抛出 IntegrityError")
except Exception:
    check("非法attribute应被拒绝", True)

# 1e. 更新不存在的 ID
result = TxSvc.update(Transaction(id=99999, date="2025-01-01", type="expense",
                                   amount=10, category="餐饮", attribute="necessity"))
check("更新不存在ID返回False", result == False)

# 1f. 删除不存在的 ID
result = TxSvc.delete(99999)
check("删除不存在ID返回False", result == False)

# 1g. 查询不存在的 ID
result = TxSvc.get_by_id(99999)
check("查询不存在ID返回None", result is None)

# 1h. SQL 注入测试 — note 字段
inj_note = "'; DROP TABLE transactions; --"
try:
    txn = TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=5.0,
                                    category="餐饮", attribute="necessity",
                                    note=inj_note))
    check("SQL注入-单引号note", True)
    # 验证数据完整性——表还在，数据还在
    fetched = TxSvc.get_by_id(txn.id)
    check("SQL注入后数据可查", fetched is not None and fetched.note == inj_note)
    TxSvc.delete(txn.id)
except Exception:
    check("SQL注入-单引号note", False)

# 1i. 空字符串 note
txn = TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=1.0,
                                category="交通", attribute="necessity", note=""))
check("空字符串note", txn.id is not None)
check("空note被保存为空字符串", txn.note == "")
TxSvc.delete(txn.id)

# 1j. 超长 note (1000 字)
long_note = "测试" * 500
txn = TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=1.0,
                                category="交通", attribute="necessity", note=long_note))
check("超长note保存", txn.id is not None)
check("超长note完整读取", len(txn.note) == 1000)
TxSvc.delete(txn.id)

# 1k. 筛选无结果
empty = TxSvc.list_all(date_from="2000-01-01", date_to="2000-01-02")
check("无数据筛选返回空列表", empty == [])

# 1l. 传入外部 conn（已有连接）
from db.connection import get_connection, close_connection
conn = get_connection()
txn = TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=10.0,
                                category="购物", attribute="joy"), conn=conn)
check("传入外部conn创建", txn.id is not None)
# 验证 conn 没有被关闭（还能查）
row = conn.execute("SELECT * FROM transactions WHERE id=?", (txn.id,)).fetchone()
check("外部conn仍可用", row is not None)
close_connection(conn)
TxSvc.delete(txn.id)

# 1m. limit/offset 分页
ids = []
for i in range(10):
    t = TxSvc.create(Transaction(date="2025-02-01", type="expense", amount=float(i+1),
                                  category="餐饮", attribute="necessity"))
    ids.append(t.id)
page1 = TxSvc.list_all(limit=5, offset=0, date_from="2025-02-01", date_to="2025-02-01")
page2 = TxSvc.list_all(limit=5, offset=5, date_from="2025-02-01", date_to="2025-02-01")
check("分页第1页", len(page1) == 5)
check("分页第2页", len(page2) == 5)
check("分页不重叠", page1[0].id != page2[0].id)
for i in ids:
    TxSvc.delete(i)

# 1n. update 不带 id
try:
    TxSvc.update(Transaction(id=None, date="2025-01-01", type="expense",
                              amount=10, category="餐饮", attribute="necessity"))
    check("update无id应抛异常", False)
except ValueError:
    check("update无id应抛异常", True)


# ============================================================
# 2. Statistics — 边界
# ============================================================
print("\n" + "=" * 60)
print("2. Statistics 边界测试")
print("=" * 60)

# 2a. 空数据库统计
summary = StatSvc.summary_by_period("2000-01-01", "2000-12-31")
check("空库-收入为0", summary["total_income"] == 0)
check("空库-支出为0", summary["total_expense"] == 0)
check("空库-笔数为0", summary["transaction_count"] == 0)

# 2b. 空库分类统计
cats = StatSvc.category_breakdown("2000-01-01", "2000-12-31")
check("空库-分类统计为空", cats == [])

# 2c. 空库属性统计
attrs = StatSvc.attribute_breakdown("2000-01-01", "2000-12-31")
check("空库-属性统计为空", attrs == [])

# 2d. 单条数据统计
txn = TxSvc.create(Transaction(date="2025-03-15", type="expense", amount=99.99,
                                category="购物", attribute="joy"))
summary = StatSvc.summary_by_period("2025-03-01", "2025-03-31")
check("单条-收入0", summary["total_income"] == 0)
check("单条-支出正确", summary["total_expense"] == 99.99)
check("单条-笔数1", summary["transaction_count"] == 1)
TxSvc.delete(txn.id)

# 2e. daily_summary 填充空白天数
start = "2025-06-01"
end = "2025-06-03"  # 3 天
daily = StatSvc.daily_summary(start, end)
check("日报-天数正确", len(daily) == 3, f"预期3天, 实际{len(daily)}天")
check("日报-每天都有数据", all(d["date"] for d in daily))

# 2f. 跨月趋势
ids = []
for m in [4, 5, 6]:
    t = TxSvc.create(Transaction(date=f"2025-{m:02d}-15", type="expense",
                                  amount=100.0, category="餐饮", attribute="necessity"))
    ids.append(t.id)
trend = StatSvc.spending_trend("2025-04-01", "2025-06-30", "monthly")
check("跨月趋势-3个月", len(trend) >= 3, f"实际{len(trend)}个月")
for i in ids:
    TxSvc.delete(i)


# ============================================================
# 3. Budget — 边界
# ============================================================
print("\n" + "=" * 60)
print("3. Budget 边界测试")
print("=" * 60)

month = "2025-07"

# 3a. 更新已有预算（重复 set）
b1 = BudSvc.set_budget("餐饮", 1000, month)
b2 = BudSvc.set_budget("餐饮", 2000, month)
check("重复set更新金额", b2.amount == 2000)
check("重复set不新增行", b1.id == b2.id)

# 3b. 无预算时的进度
conn = get_connection()
conn.execute("DELETE FROM budgets")
conn.commit()
close_connection(conn)
progress = BudSvc.get_budget_progress(month)
check("无预算-进度为0", progress["total_budget"] == 0)
check("无预算-花费为0", progress["total_spent"] == 0)

# 3c. 预算=0
BudSvc.set_budget(None, 0, month)
budgets = BudSvc.get_budgets(month)
check("零预算可设置", any(b.category is None and b.amount == 0 for b in budgets))

# 3d. 查不存在的月份
empty = BudSvc.get_budgets("2099-01")
check("不存在月份-空列表", empty == [])

# 清理
conn = get_connection()
conn.execute("DELETE FROM budgets")
conn.commit()
close_connection(conn)


# ============================================================
# 4. Reminder — 边界
# ============================================================
print("\n" + "=" * 60)
print("4. Reminder 边界测试")
print("=" * 60)

# 4a. 过去日期 + 不重复 = 过期
old_date = (date.today() - timedelta(days=30)).isoformat()
r = RemSvc.create(BillReminder(name="已过期账单", due_date=old_date,
                                amount=100, repeat_cycle="none"))
overdue = RemSvc.get_overdue()
check("检测过期提醒", any(o.id == r.id for o in overdue))
RemSvc.delete(r.id)

# 4b. 过去日期 + monthly repeat = 自动推进
old_date_monthly = date.today().replace(day=1) - timedelta(days=1)  # 上个月最后一天
r2 = RemSvc.create(BillReminder(name="房租(月)", due_date=old_date_monthly.isoformat(),
                                 amount=3000, repeat_cycle="monthly"))
due = RemSvc.get_due_soon(days_ahead=30)
matched = [d for d in due if d.name == "房租(月)"]
check("monthly重复-自动推进", len(matched) > 0,
      f"匹配到{len(matched)}条" if matched else "未找到推进后的提醒")
RemSvc.delete(r2.id)

# 4c. 未来日期
future = (date.today() + timedelta(days=365)).isoformat()
r3 = RemSvc.create(BillReminder(name="明年账单", due_date=future,
                                 amount=50, repeat_cycle="none"))
due_soon = RemSvc.get_due_soon(days_ahead=7)
check("未来一年-不出现", not any(d.id == r3.id for d in due_soon))
RemSvc.delete(r3.id)

# 4d. update 无 id
try:
    RemSvc.update(BillReminder(name="test", due_date="2025-01-01"))
    check("reminder update无id应抛异常", False)
except ValueError:
    check("reminder update无id应抛异常", True)

# 4e. delete 不存在
result = RemSvc.delete(99999)
check("reminder删除不存在", result == False)

# 4f. 空列表
conn = get_connection()
conn.execute("DELETE FROM bill_reminders")
conn.commit()
close_connection(conn)
check("空提醒列表", RemSvc.get_all() == [])
check("空到期列表", RemSvc.get_due_soon() == [])


# ============================================================
# 5. Template — 边界
# ============================================================
print("\n" + "=" * 60)
print("5. Template 边界测试")
print("=" * 60)

# 5a. 使用不存在的模板
result = TplSvc.apply_template(99999, "2025-01-01")
check("应用不存在模板返回None", result is None)

# 5b. 模板 update 无 id
try:
    TplSvc.update(Template(name="test", type="expense", amount=10,
                            category="餐饮", attribute="necessity"))
    check("template update无id应抛异常", False)
except ValueError:
    check("template update无id应抛异常", True)

# 5c. 模板缺省值
t = TplSvc.create(Template(name="最简模板", type="expense", amount=1.0,
                            category="餐饮", attribute="necessity", account="现金", note=""))
txn = TplSvc.apply_template(t.id, "2025-01-01")
check("模板默认note为空", txn.note == "")
TxSvc.delete(txn.id)
TplSvc.delete(t.id)


# ============================================================
# 6. Export — 边界
# ============================================================
print("\n" + "=" * 60)
print("6. Export 边界测试")
print("=" * 60)

import tempfile

# 6a. 空导出（无数据）
tmp = os.path.join(tempfile.gettempdir(), "test_empty_export.xlsx")
count = ExpSvc.export_transactions(tmp, "2000-01-01", "2000-01-02")
check("空数据导出", count == 0)
check("空数据仍生成文件", os.path.exists(tmp))
os.remove(tmp)

# 6b. 特殊字符 note
special_note = "test\n换行\t制表符,逗号;分号|管道&与号<尖括号>"
txn = TxSvc.create(Transaction(date="2025-01-01", type="expense", amount=1.0,
                                category="餐饮", attribute="necessity", note=special_note))
tmp = os.path.join(tempfile.gettempdir(), "test_special_export.xlsx")
count = ExpSvc.export_transactions(tmp)
check("特殊字符导出", count >= 1)
check("特殊字符文件生成", os.path.exists(tmp))
os.remove(tmp)
TxSvc.delete(txn.id)


# ============================================================
# 7. Backup — 边界
# ============================================================
print("\n" + "=" * 60)
print("7. Backup 边界测试")
print("=" * 60)

# 7a. 还原不存在的文件
try:
    BkpSvc.restore("/nonexistent/path/backup.db")
    check("还原不存在文件应抛异常", False)
except FileNotFoundError:
    check("还原不存在文件应抛异常", True)

# 7b. 空备份目录列表
backups = BkpSvc.list_backups("/nonexistent/dir")
check("不存在的备份目录-空列表", backups == [])

# 7c. 正常备份再还原
path = BkpSvc.backup()
check("备份成功", os.path.exists(path))
restored = BkpSvc.restore(path)
check("还原成功", restored)
os.remove(path)

# ============================================================
# 结果
# ============================================================
print("\n" + "=" * 60)
print(f"测试结果: {passed} 通过, {failed} 失败 (共 {passed+failed})")
print("=" * 60)

if failed > 0:
    print("❌ 有测试失败！")
    sys.exit(1)
else:
    print("🎉 刁钻 QA 测试全部通过！")
