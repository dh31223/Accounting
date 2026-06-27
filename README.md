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
├── core/                    # 业务逻辑层（阶段 2）
├── ui/                      # PyQt 界面层（阶段 4+）
├── assets/icons/            # 图标资源
├── design/                  # UI 设计原型
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
| 2 | ⬜ 待做 | 核心业务逻辑层 |
| 3 | ⬜ 待做 | UI 界面原型（HTML） |
| 4 | ⬜ 待做 | PyQt 主窗口 + 交易管理 |
| 5 | ⬜ 待做 | 统计仪表盘 |
| 6 | ⬜ 待做 | 预算 + 账单提醒 |
| 7 | ⬜ 待做 | 模板 + 导出 + 备份 |
| 8 | ⬜ 待做 | AI 预算建议（可选） |

## 属性标签

| 标签 | 含义 |
|------|------|
| 💚 值得 | 必要且情绪 — 确实需要，买了开心 |
| 💛 悦己 | 不必要且情绪 — 纯粹情绪价值 |
| 📋 刚需 | 必要且不情绪 — 必须花但不会开心 |
| 🚫 浪费 | 不必要且不情绪 — 罚款/被骗/货不对板 |
