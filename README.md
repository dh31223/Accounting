# Accounting — 个人记账软件

基于 Python + PyQt6 + SQLite 的个人财务管理工具，支持收支记录、统计分析、预算管理和账单提醒。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12+ | 开发语言 |
| PyQt6 (系统包) | 图形界面（深色主题） |
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
│   ├── backup.py            # 数据库备份/还原
│   └── ai_suggest.py        # AI 预算建议 (DeepSeek API)
├── ui/
│   ├── theme.py             # 深色主题 QSS 样式表
│   ├── main_window.py       # 主窗口框架（侧边导航 + QStackedWidget）
│   ├── transaction_panel.py # 交易记录页（树状结构 + 筛选栏）
│   ├── transaction_dialog.py# 添加/编辑交易模态弹窗
│   ├── dashboard.py         # 统计仪表盘（matplotlib 图表）
│   ├── budget_panel.py      # 预算管理（总预算 + 分项进度条）
│   ├── reminder_panel.py    # 账单提醒（到期检测 + 列表管理）
│   ├── template_panel.py    # 交易模板（列表 + 一键录入 + CRUD）
│   ├── settings_dialog.py   # 设置（Excel 导出 + 备份/还原）
│   └── ai_panel.py          # AI 预算建议（DeepSeek 集成）
├── design/                  # UI 设计参考 (gitignored)
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
# 1. 安装系统依赖（PyQt6 + fcitx 中文输入法插件使用同一 Qt 6.4 ABI）
sudo apt-get install -y python3-pyqt6 python3-pyqt6.qtcharts \
    python3-matplotlib python3-openpyxl python3-httpx

# 2. 创建虚拟环境（需访问系统包）
uv venv --system-site-packages

# 3. （可选）配置 AI 预算建议功能
cp APIKey.txt.example APIKey.txt
# 编辑 APIKey.txt，填入你的 DeepSeek API Key（https://platform.deepseek.com）
# 或者设置环境变量: export DEEPSEEK_API_KEY="sk-..."

# 4. 运行
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
| 5 | ✅ 完成 | 统计仪表盘 |
| 6 | ✅ 完成 | 预算 + 账单提醒 |
| 7 | ✅ 完成 | 模板 + 导出 + 备份 |
| 8 | ✅ 完成 | AI 预算建议 (DeepSeek API) |

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

### 统计仪表盘 (阶段 5)
- **统计卡片**: 收入（绿）/ 支出（红）/ 结余（靛蓝），数字大字号突出
- **消费趋势折线图**: 日/周/月 切换按钮，支出红色线 + 收入绿色线
- **支出分类占比饼图**: 自动着色，图例标签
- **属性分布饼图**: 值得/悦己/刚需/浪费 四象限统计
- **自定义日期范围**: 从/至 日期选择 + 统计按钮，刷新全部图表
- **matplotlib 深色主题**: 图表背景匹配应用暗色，中文字体 Noto Sans CJK SC

### 预算管理 (阶段 6)
- **总预算设定**: 月份选择器 + 总预算金额 + 进度条（正常蓝 / 超支红）
- **分项预算**: 2 列网格，每分类独立卡片（预算金额 + 实际支出 + 进度条）
- **超支检测**: 超支时顶部红色警告条，列出超支分类明细
- **一键设定**: 点击「设定」弹出金额对话框，支持总预算和分类预算

### 账单提醒 (阶段 6)
- **提醒列表**: 名称 / 金额 / 到期日 / 周期 / 备注，5 列表格
- **到期标记**: 已过期红色 `⚠ 已过期` / 7天内到期黄色 `⏰`
- **到期汇总卡片**: 顶部聚合显示所有异常提醒
- **添加/编辑弹窗**: 名称 / 金额 / 到期日 / 重复周期 / 备注
- **右键操作**: 编辑 / 删除（含确认弹窗）

### 交易模板 (阶段 7)
- **模板列表**: 7 列表格（名称 / 类型 / 金额 / 分类 / 属性 / 账户 / 备注）
- **一键录入**: 选中模板 → 点击按钮 → 确认后自动创建交易
- **添加/编辑弹窗**: 类型联动分类、金额验证、属性选择

### 设置 (阶段 7)
- **Excel 导出**: 日期范围选择 → 文件保存对话框 → openpyxl 生成 .xlsx
- **数据库备份**: 一键备份到 backups/ 目录（WAL checkpoint）
- **数据库还原**: 选择备份文件 → 安全确认 → 自动先备份当前库再还原
- **备份列表**: 显示历史备份文件名 / 大小 / 时间

### AI 预算建议 (阶段 8)
- **数据聚合**: 本地聚合近 3 个月收支摘要（仅发送几百 tokens，成本极低）
- **DeepSeek API**: 兼容 OpenAI 格式，`deepseek-chat` 模型
- **自定义提示词**: 内置专业理财顾问提示词，可自由编辑 + 一键恢复默认
- **后台线程**: 避免阻塞 UI，加载时显示进度条
- **Markdown 展示**: 结果以富文本呈现（整体评估 + 分类建议 + 优化方向 + 预算模板表）
- **API Key 管理**: 支持环境变量 `DEEPSEEK_API_KEY` + 界面输入 + 密码隐藏

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
