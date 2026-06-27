# Accounting — 个人记账软件

基于 Python + PyQt6 + SQLite 的个人财务管理工具，支持收支记录、统计分析、预算管理和账单提醒。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.13+ | 开发语言 |
| PyQt6 | 图形界面（深色主题） |
| SQLite | 本地数据库 |
| matplotlib | 统计图表 |
| openpyxl | Excel 导出 |
| httpx | AI 预算建议（可选） |

## 项目结构

```
Accounting/
├── main.py                  # 入口
├── db/
│   ├── connection.py        # SQLite 连接管理 (WAL + 外键)
│   └── schema.py            # 建表 + 预设分类初始化
├── core/
│   ├── models.py            # 数据模型 (Transaction/Budget/Reminder/Template)
│   ├── transaction.py       # 交易 CRUD 服务
│   ├── statistics.py        # 统计引擎 (日/周/月/年聚合)
│   ├── budget.py            # 预算管理 + 超支检测
│   ├── reminder.py          # 账单提醒 + 到期检测
│   ├── template.py          # 交易模板 + 一键录入
│   ├── export.py            # Excel 导出 (openpyxl)
│   └── backup.py            # 数据库备份/还原
├── ui/
│   ├── theme.py             # 深色主题 QSS 样式表
│   ├── main_window.py       # 主窗口框架（侧边导航 + QStackedWidget）
│   ├── transaction_panel.py # 交易记录页（树状结构 + 筛选栏）
│   └── transaction_dialog.py# 添加/编辑交易模态弹窗
├── design/
│   └── prototype.html       # 高保真 UI 设计原型
├── test_phase2.py           # 阶段 2 功能测试
├── test_qa_strict.py        # 阶段 2 QA 严格测试（55 项）
├── SPEC.md                  # 完整需求规格书 (gitignored)
└── accounting.db            # 数据库文件 (gitignored)
```

## 数据库结构

### transactions — 交易记录
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| date | DATE | 发生日期 |
| type | TEXT | income / expense |
| amount | REAL | 金额 |
| category | TEXT | 分类 |
| attribute | TEXT | worthy / joy / necessity / waste |
| note | TEXT | 备注 |
| account | TEXT | 账户 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### categories — 分类
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT UNIQUE | 分类名 |
| type | TEXT | income / expense |
| is_default | INTEGER | 是否预设分类 |

**预设支出分类**: 餐饮、交通、购物、住房、娱乐、医疗、发红包
**预设收入分类**: 工资、收红包、兼职、理财、生活费

### budgets — 预算
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| category | TEXT | NULL=总预算 |
| amount | REAL | 预算金额 |
| period_month | TEXT | 月份 '2025-06' |

### bill_reminders — 账单提醒
| 字段 | 类型 | 说明 |
|------|------|------|
| name | TEXT | 账单名称 |
| amount | REAL | 金额 |
| due_date | DATE | 到期日 |
| repeat_cycle | TEXT | none / monthly / yearly |

### templates — 交易模板
| 字段 | 类型 | 说明 |
|------|------|------|
| name | TEXT | 模板名称 |
| type | TEXT | income / expense |
| amount | REAL | 默认金额 |
| category | TEXT | 默认分类 |
| attribute | TEXT | 默认属性 |
| account | TEXT | 默认账户 |
| note | TEXT | 默认备注 |

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
uv venv
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple pyqt6 matplotlib openpyxl httpx

# 2. 运行
uv run python main.py

# 首次运行会自动创建 accounting.db 并插入预设分类
```

## 开发阶段

| 阶段 | 状态 | 内容 |
|------|------|------|
| 1 | ✅ 完成 | 项目初始化 + 数据库设计 |
| 2 | ✅ 完成 | 核心业务逻辑层 (7 个 Service) |
| 3 | ✅ 完成 | UI 设计原型 (HTML 高保真) |
| 4 | ✅ 完成 | PyQt 主窗口 + 交易管理 |
| 5 | ⬜ 待做 | 统计仪表盘 |
| 6 | ⬜ 待做 | 预算 + 账单提醒 |
| 7 | ⬜ 待做 | 模板 + 导出 + 备份 |
| 8 | ⬜ 待做 | AI 预算建议（可选） |

## GUI 界面 (阶段 4+)

### 主窗口布局
- 左侧深色侧边导航栏（200px），含 Logo + 6 个导航按钮（交易记录/统计仪表盘/预算管理/账单提醒/交易模板/设置）
- 右侧 QStackedWidget 页面切换
- 底部状态栏显示实时反馈

### 交易记录页
- **树状结构**: 年 → 月 → 周 → 日，每层显示收支汇总数字
- **顶部筛选栏**: 日期范围、类型、分类、账户、属性，一键查询
- **右键菜单**: 编辑 / 删除交易（含确认弹窗）
- **浮动添加按钮**: 右下角 ＋ 按钮（Ctrl+N 快捷键）
- **添加/编辑弹窗**: 日期选择、收入/支出切换、金额、分类、属性、账户、备注

### 深色主题设计
- 背景 `#1a1a2e` / 侧边栏 `#0f0f23` / 卡片 `#16213e`
- 强调色 `#818cf8` (indigo) / 收入绿 `#34d399` / 支出红 `#f87171`
- QSS 全局样式覆盖，圆角卡片、平滑过渡

## Core API 快速参考

```python
# 交易 CRUD
from core.transaction import add_transaction, list_transactions, update_transaction, delete_transaction
txn = add_transaction("2025-06-27", "expense", 35.5, "餐饮", "necessity", "午饭", "支付宝")
records = list_transactions(date_from="2025-06-01", date_to="2025-06-30", txn_type="expense")

# 统计分析
from core.statistics import StatisticsService, current_month_range
summary = StatisticsService.summary_by_period("2025-06-01", "2025-06-30")
trend = StatisticsService.spending_trend("2025-06-01", "2025-06-30", "daily")
cats = StatisticsService.category_breakdown("2025-06-01", "2025-06-30", "expense")

# 预算
from core.budget import BudgetService
BudgetService.set_budget(None, 5000, "2025-06")  # 总预算
BudgetService.set_budget("餐饮", 2000, "2025-06")  # 分类预算
overspent = BudgetService.check_overspend("2025-06")

# 账单提醒
from core.reminder import ReminderService
due = ReminderService.get_due_soon(days_ahead=7)

# 模板
from core.template import TemplateService
txn = TemplateService.apply_template(template_id, "2025-06-27")

# 导出 & 备份
from core.export import ExportService
ExportService.export_transactions("output.xlsx", "2025-01-01", "2025-06-30")
from core.backup import BackupService
BackupService.backup()
```

## 属性标签

| 标签 | 含义 |
|------|------|
| 💚 值得 | 必要且情绪 — 确实需要，买了开心 |
| 💛 悦己 | 不必要且情绪 — 纯粹情绪价值 |
| 📋 刚需 | 必要且不情绪 — 必须花但不会开心 |
| 🚫 浪费 | 不必要且不情绪 — 罚款/被骗/货不对板 |
