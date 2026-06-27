"""数据库 Schema 定义与初始化。

包含建表语句、预设分类数据插入、数据库初始化入口。
"""

from db.connection import get_connection, close_connection, db_exists

# ============================================================
# 建表 SQL
# ============================================================

CREATE_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE    NOT NULL,
    type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
    amount      REAL    NOT NULL CHECK(amount > 0),
    category    TEXT    NOT NULL,
    attribute   TEXT    NOT NULL CHECK(attribute IN ('worthy', 'joy', 'necessity', 'waste')),
    note        TEXT    DEFAULT '',
    account     TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CATEGORIES = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
    is_default  INTEGER DEFAULT 1
);
"""

CREATE_BUDGETS = """
CREATE TABLE IF NOT EXISTS budgets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category        TEXT,       -- NULL 表示总预算
    amount          REAL    NOT NULL,
    period_month    TEXT    NOT NULL  -- 格式: '2025-06'
);
"""

CREATE_BILL_REMINDERS = """
CREATE TABLE IF NOT EXISTS bill_reminders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    amount          REAL,
    due_date        DATE    NOT NULL,
    repeat_cycle    TEXT    DEFAULT 'none',  -- none / monthly / yearly
    note            TEXT    DEFAULT ''
);
"""

CREATE_TEMPLATES = """
CREATE TABLE IF NOT EXISTS templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    attribute   TEXT    NOT NULL,
    account     TEXT    NOT NULL,
    note        TEXT    DEFAULT ''
);
"""

# ============================================================
# 索引
# ============================================================

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);",
    "CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(type);",
    "CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category);",
    "CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account);",
    "CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period_month);",
    "CREATE INDEX IF NOT EXISTS idx_reminders_due ON bill_reminders(due_date);",
]

# ============================================================
# 预设分类数据
# ============================================================

PRESET_EXPENSE_CATEGORIES = [
    "餐饮", "交通", "购物", "住房", "娱乐", "医疗", "发红包",
]

PRESET_INCOME_CATEGORIES = [
    "工资", "收红包", "兼职", "理财", "生活费",
]

PRESET_ACCOUNTS = [
    "现金", "银行卡", "支付宝", "微信",
]

ALL_TABLES = [CREATE_TRANSACTIONS, CREATE_CATEGORIES, CREATE_BUDGETS,
              CREATE_BILL_REMINDERS, CREATE_TEMPLATES]

# ============================================================
# 初始化函数
# ============================================================


def init_db() -> None:
    """初始化数据库：建表、建索引、插入预设分类。
    如果数据库已存在则跳过初始化。
    """
    conn = get_connection()

    try:
        # 1. 建表
        for sql in ALL_TABLES:
            conn.execute(sql)

        # 2. 建索引
        for sql in CREATE_INDEXES:
            conn.execute(sql)

        # 3. 插入预设分类（如果 categories 表为空）
        cursor = conn.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        if count == 0:
            _insert_preset_categories(conn)

        conn.commit()
        print(f"[OK] 数据库初始化完成: {conn.execute('PRAGMA database_list').fetchone()['file']}")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        close_connection(conn)


def _insert_preset_categories(conn) -> None:
    """插入预设收支分类。"""
    for name in PRESET_EXPENSE_CATEGORIES:
        conn.execute(
            "INSERT INTO categories (name, type, is_default) VALUES (?, 'expense', 1)",
            (name,)
        )
    for name in PRESET_INCOME_CATEGORIES:
        conn.execute(
            "INSERT INTO categories (name, type, is_default) VALUES (?, 'income', 1)",
            (name,)
        )
    print(f"[OK] 已插入 {len(PRESET_EXPENSE_CATEGORIES)} 个支出分类, "
          f"{len(PRESET_INCOME_CATEGORIES)} 个收入分类")


def get_all_categories(conn=None) -> dict:
    """获取全部分类，按类型分组。

    Returns:
        dict: {'expense': [...], 'income': [...]}
    """
    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    try:
        expense = [row["name"] for row in
                   conn.execute("SELECT name FROM categories WHERE type='expense' ORDER BY id")]
        income = [row["name"] for row in
                  conn.execute("SELECT name FROM categories WHERE type='income' ORDER BY id")]
        return {"expense": expense, "income": income}
    finally:
        if own_conn:
            close_connection(conn)


def get_all_accounts() -> list:
    """获取全部账户列表。"""
    return list(PRESET_ACCOUNTS)
