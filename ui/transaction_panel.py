"""交易记录面板。

树状结构展示交易历史：年 → 月 → 周 → 日
顶部筛选栏 + 浮动添加按钮 + 右键编辑/删除
"""

from datetime import date, timedelta
from collections import defaultdict
from calendar import monthrange

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QDateEdit, QComboBox, QPushButton, QLabel, QMenu, QMessageBox,
    QAbstractItemView, QHeaderView, QApplication,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QAction, QCursor

from core.transaction import TransactionService
from core.models import Transaction
from ui.transaction_dialog import TransactionDialog
from db.schema import get_all_categories, get_all_accounts

# 属性标签映射
ATTRIBUTE_LABELS = {
    "worthy": "💚值得",
    "joy": "💛悦己",
    "necessity": "📋刚需",
    "waste": "🚫浪费",
}


def _get_week_range(d: date):
    """返回 d 所在周的周一和周日。"""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _week_number(d: date):
    """返回日期在当年的周数（ISO 周）。"""
    return d.isocalendar()[1]


class TransactionPanel(QWidget):
    """交易记录面板。

    Signals:
        status_message(str): 状态栏消息
    """

    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_filters()
        self.refresh()

    # ---- UI 构建 ----

    def _setup_ui(self):
        """构建面板 UI。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # 页面标题
        title = QLabel("📂 交易记录")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ---- 筛选栏（两行）----
        filter_widget = QWidget()
        filter_widget.setObjectName("card")
        filter_outer = QVBoxLayout(filter_widget)
        filter_outer.setContentsMargins(16, 10, 16, 10)
        filter_outer.setSpacing(8)

        # 第一行：日期范围
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self._add_filter_label(row1, "从")

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setMinimumWidth(130)
        row1.addWidget(self._date_from)

        self._add_filter_label(row1, "至")

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setMinimumWidth(130)
        row1.addWidget(self._date_to)

        row1.addStretch()
        filter_outer.addLayout(row1)

        # 第二行：类型 / 分类 / 账户 / 属性 / 查询
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # 类型筛选
        self._add_filter_label(row2, "类型")
        self._type_filter = QComboBox()
        self._type_filter.setMinimumWidth(100)
        self._type_filter.setMaxVisibleItems(10)
        self._type_filter.addItem("全部", None)
        self._type_filter.addItem("💰 收入", "income")
        self._type_filter.addItem("💸 支出", "expense")
        row2.addWidget(self._type_filter)

        # 分类筛选
        self._add_filter_label(row2, "分类")
        self._category_filter = QComboBox()
        self._category_filter.setMinimumWidth(120)
        self._category_filter.setMaxVisibleItems(10)
        row2.addWidget(self._category_filter)

        # 账户筛选
        self._add_filter_label(row2, "账户")
        self._account_filter = QComboBox()
        self._account_filter.setMinimumWidth(100)
        self._account_filter.setMaxVisibleItems(10)
        row2.addWidget(self._account_filter)

        # 属性筛选
        self._add_filter_label(row2, "属性")
        self._attr_filter = QComboBox()
        self._attr_filter.setMinimumWidth(110)
        self._attr_filter.setMaxVisibleItems(10)
        self._attr_filter.addItem("全部", None)
        for key, label in ATTRIBUTE_LABELS.items():
            self._attr_filter.addItem(label, key)
        row2.addWidget(self._attr_filter)

        # 查询按钮
        search_btn = QPushButton("🔍 查询")
        search_btn.setObjectName("btnSmall")
        search_btn.clicked.connect(self.refresh)
        row2.addWidget(search_btn)

        row2.addStretch()
        filter_outer.addLayout(row2)

        layout.addWidget(filter_widget)

        # ---- 树形控件 ----
        self._tree = QTreeWidget()
        self._tree.setColumnCount(7)
        self._tree.setHeaderLabels([
            "日期", "类型", "金额", "分类", "属性", "账户", "备注"
        ])
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # 列宽
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        layout.addWidget(self._tree, stretch=1)

        # ---- 浮动添加按钮 ----
        fab_layout = QHBoxLayout()
        fab_layout.addStretch()
        add_btn = QPushButton("＋")
        add_btn.setObjectName("btnFab")
        add_btn.setToolTip("添加交易 (Ctrl+N)")
        add_btn.clicked.connect(self._on_add)
        add_btn.setShortcut("Ctrl+N")
        fab_layout.addWidget(add_btn)
        layout.addLayout(fab_layout)

    def _add_filter_label(self, layout: QHBoxLayout, text: str):
        """添加筛选栏标签（无背景无边框）。"""
        label = QLabel(f"{text}:")
        label.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 13px; "
            "border: none; padding: 0px; margin: 0px;"
        )
        layout.addWidget(label)

    # ---- 筛选数据加载 ----

    def _load_filters(self):
        """加载筛选下拉的数据。"""
        cats = get_all_categories()

        # 分类筛选
        self._category_filter.addItem("全部", None)
        for name in cats.get("expense", []):
            self._category_filter.addItem(f"📤 {name}", name)
        for name in cats.get("income", []):
            self._category_filter.addItem(f"📥 {name}", name)

        # 账户筛选
        self._account_filter.addItem("全部", None)
        for acc in get_all_accounts():
            self._account_filter.addItem(acc)

    # ---- 数据刷新 ----

    def refresh(self):
        """重新加载数据。"""
        self._tree.clear()

        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")
        txn_type = self._type_filter.currentData()
        category = self._category_filter.currentData()
        account = self._account_filter.currentData()
        attribute = self._attr_filter.currentData()

        transactions = TransactionService.list_all(
            date_from=date_from,
            date_to=date_to,
            txn_type=txn_type,
            category=category,
            account=account,
            attribute=attribute,
            order_by="date DESC, id DESC",
            limit=2000,
        )

        if not transactions:
            empty = QTreeWidgetItem(self._tree)
            empty.setText(0, "暂无交易记录")
            empty.setText(1, "点击 ＋ 按钮添加第一条记录")
            self._tree.addTopLevelItem(empty)
            self.status_message.emit("暂无符合条件的交易记录")
            return

        self._build_tree(transactions)
        self.status_message.emit(f"显示 {len(transactions)} 条交易记录")

    def _build_tree(self, transactions: list[Transaction]):
        """构建年→月→周→日 树状结构。"""
        # 按 年 → 月 → 周 → 日 分组
        groups: dict[str, dict[str, dict[str, dict[str, list[Transaction]]]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

        for txn in transactions:
            d = date.fromisoformat(txn.date)
            year_key = str(d.year)
            month_key = f"{d.month:02d}"
            monday, sunday = _get_week_range(d)
            week_key = f"{_week_number(d):02d}_{monday.isoformat()}_{sunday.isoformat()}"
            day_key = d.isoformat()
            groups[year_key][month_key][week_key][day_key].append(txn)

        total_count = 0

        # 按年份降序
        for year_key in sorted(groups.keys(), reverse=True):
            year_data = groups[year_key]
            year_income = 0.0
            year_expense = 0.0

            # 先遍历计算年度汇总
            for m_key, m_data in year_data.items():
                for w_key, w_data in m_data.items():
                    for d_key, d_txns in w_data.items():
                        for txn in d_txns:
                            if txn.type == "income":
                                year_income += txn.amount
                            else:
                                year_expense += txn.amount

            year_balance = year_income - year_expense
            year_item = QTreeWidgetItem(self._tree)
            year_item.setText(0, f"📅 {year_key}年")
            year_item.setText(1, f"收入 ¥{year_income:,.2f}")
            year_item.setText(2, f"支出 ¥{year_expense:,.2f}")
            year_item.setText(3, f"结余 ¥{year_balance:,.2f}")
            year_item.setData(0, Qt.ItemDataRole.UserRole, "year")

            # 按月份降序
            for month_key in sorted(year_data.keys(), reverse=True):
                month_txns_dict = year_data[month_key]
                month_income = 0.0
                month_expense = 0.0

                for week_key, week_data in month_txns_dict.items():
                    for day_key, day_txns in week_data.items():
                        for txn in day_txns:
                            if txn.type == "income":
                                month_income += txn.amount
                            else:
                                month_expense += txn.amount

                month_balance = month_income - month_expense
                month_item = QTreeWidgetItem(year_item)
                month_item.setText(0, f"📆 {int(month_key)}月")
                month_item.setText(1, f"收入 ¥{month_income:,.2f}")
                month_item.setText(2, f"支出 ¥{month_expense:,.2f}")
                month_item.setText(3, f"结余 ¥{month_balance:,.2f}")
                month_item.setData(0, Qt.ItemDataRole.UserRole, "month")

                # 按周降序
                week_keys = sorted(month_txns_dict.keys(), reverse=True)
                for week_key in week_keys:
                    week_data = month_txns_dict[week_key]
                    parts = week_key.split("_", 2)
                    week_num = int(parts[0])
                    monday_str = parts[1]
                    sunday_str = parts[2]

                    week_income = 0.0
                    week_expense = 0.0
                    for day_key, day_txns in week_data.items():
                        for txn in day_txns:
                            if txn.type == "income":
                                week_income += txn.amount
                            else:
                                week_expense += txn.amount

                    week_balance = week_income - week_expense
                    week_item = QTreeWidgetItem(month_item)
                    week_item.setText(0, f"📋 第{week_num}周 {monday_str[5:]}~{sunday_str[5:]}")
                    week_item.setText(1, f"收入 ¥{week_income:,.2f}")
                    week_item.setText(2, f"支出 ¥{week_expense:,.2f}")
                    week_item.setText(3, f"结余 ¥{week_balance:,.2f}")
                    week_item.setData(0, Qt.ItemDataRole.UserRole, "week")

                    # 按日期降序
                    for day_key in sorted(week_data.keys(), reverse=True):
                        day_txns = week_data[day_key]
                        day_d = date.fromisoformat(day_key)
                        weekday_name = ["一", "二", "三", "四", "五", "六", "日"][day_d.weekday()]

                        # 日汇总行
                        day_item = QTreeWidgetItem(week_item)
                        day_income = sum(t.amount for t in day_txns if t.type == "income")
                        day_expense = sum(t.amount for t in day_txns if t.type == "expense")
                        day_item.setText(0, f"{day_key} 周{weekday_name}")
                        day_item.setText(1, f"收入 ¥{day_income:,.2f}" if day_income > 0 else "")
                        day_item.setText(2, f"支出 ¥{day_expense:,.2f}" if day_expense > 0 else "")
                        day_item.setText(3, f"{len(day_txns)} 笔")
                        day_item.setData(0, Qt.ItemDataRole.UserRole, "day")

                        # 具体交易行
                        for txn in day_txns:
                            txn_item = QTreeWidgetItem(day_item)
                            txn_type_label = "💰 收入" if txn.type == "income" else "💸 支出"
                            amount_text = f"+¥{txn.amount:,.2f}" if txn.type == "income" else f"-¥{txn.amount:,.2f}"

                            txn_item.setText(0, txn.date)
                            txn_item.setText(1, txn_type_label)
                            txn_item.setText(2, amount_text)
                            txn_item.setText(3, txn.category)
                            txn_item.setText(4, ATTRIBUTE_LABELS.get(txn.attribute, txn.attribute))
                            txn_item.setText(5, txn.account)
                            txn_item.setText(6, txn.note)

                            # 收入绿色，支出红色
                            if txn.type == "income":
                                txn_item.setForeground(2, Qt.GlobalColor.darkGreen)
                            else:
                                txn_item.setForeground(2, Qt.GlobalColor.red)

                            txn_item.setData(0, Qt.ItemDataRole.UserRole, ("txn", txn.id))
                            total_count += 1

        # 默认展开到月级别
        for i in range(self._tree.topLevelItemCount()):
            year_item = self._tree.topLevelItem(i)
            self._tree.expandItem(year_item)
            # 展开最近一个月
            if year_item.childCount() > 0:
                month_item = year_item.child(0)
                self._tree.expandItem(month_item)
                # 展开最近一周
                if month_item.childCount() > 0:
                    week_item = month_item.child(0)
                    self._tree.expandItem(week_item)

        self.status_message.emit(f"显示 {total_count} 条交易记录")

    # ---- 交互事件 ----

    def _on_add(self):
        """打开添加交易对话框。"""
        try:
            dlg = TransactionDialog(self)
            # 确保对话框在父窗口范围内显示
            dlg.adjustSize()
            if self.window():
                parent_geo = self.window().frameGeometry()
                dlg_geo = dlg.frameGeometry()
                dlg_geo.moveCenter(parent_geo.center())
                dlg.move(dlg_geo.topLeft())
            if dlg.exec() == TransactionDialog.DialogCode.Accepted:
                self.refresh()
                self.status_message.emit("交易已添加")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开对话框: {e}")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击编辑交易。"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, tuple) and data[0] == "txn":
            txn_id = data[1]
            self._edit_transaction(txn_id)

    def _on_context_menu(self, pos):
        """右键菜单。"""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, tuple) or data[0] != "txn":
            return

        txn_id = data[1]

        menu = QMenu(self)
        edit_action = menu.addAction("✏️ 编辑")
        delete_action = menu.addAction("🗑 删除")

        action = menu.exec(QCursor.pos())
        if action == edit_action:
            self._edit_transaction(txn_id)
        elif action == delete_action:
            self._delete_transaction(txn_id)

    # ---- CRUD 操作 ----

    def _edit_transaction(self, txn_id: int):
        """编辑交易。"""
        try:
            txn = TransactionService.get_by_id(txn_id)
            if not txn:
                QMessageBox.warning(self, "错误", "交易记录不存在")
                return

            dlg = TransactionDialog(self, transaction=txn)
            dlg.adjustSize()
            if self.window():
                parent_geo = self.window().frameGeometry()
                dlg_geo = dlg.frameGeometry()
                dlg_geo.moveCenter(parent_geo.center())
                dlg.move(dlg_geo.topLeft())
            if dlg.exec() == TransactionDialog.DialogCode.Accepted:
                self.refresh()
                self.status_message.emit("交易已更新")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {e}")

    def _delete_transaction(self, txn_id: int):
        """删除交易（含确认）。"""
        txn = TransactionService.get_by_id(txn_id)
        if not txn:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除这条交易记录吗？\n\n"
            f"日期: {txn.date}\n"
            f"金额: ¥{txn.amount:,.2f}\n"
            f"分类: {txn.category}\n\n"
            f"此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                TransactionService.delete(txn_id)
                self.refresh()
                self.status_message.emit("交易已删除")
            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"数据库错误: {e}")
