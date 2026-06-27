"""添加/编辑交易对话框。

模态弹窗，包含完整表单：
- 日期选择 / 类型切换 / 金额输入 / 分类下拉 / 属性下拉 / 账户下拉 / 备注
"""

from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDateEdit, QComboBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QButtonGroup,
    QRadioButton, QWidget, QApplication,
)
from PyQt6.QtCore import Qt, QDate

from core.models import Transaction
from core.transaction import TransactionService
from db.schema import get_all_categories, get_all_accounts

# 属性选项
ATTRIBUTES = {
    "worthy": "💚 值得",
    "joy": "💛 悦己",
    "necessity": "📋 刚需",
    "waste": "🚫 浪费",
}


class TransactionDialog(QDialog):
    """添加/编辑交易对话框。"""

    def __init__(self, parent=None, transaction: Transaction = None):
        super().__init__(parent)
        self._txn = transaction  # None = 新增, 非 None = 编辑
        self._result_txn = None

        self._setup_ui()
        self._load_categories()
        self._load_accounts()

        if transaction:
            self._populate(transaction)

    # ---- 属性 ----

    @property
    def result_transaction(self) -> Transaction | None:
        """对话框确认后返回的 Transaction 对象。"""
        return self._result_txn

    # ---- UI 构建 ----

    def _setup_ui(self):
        """构建对话框 UI。"""
        title = "编辑交易" if self._txn else "添加交易"
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 24)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:18px; font-weight:bold; color:#e2e8f0;")
        layout.addWidget(title_label)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 日期
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("日期:", self._date_edit)

        # 类型（收入/支出 切换按钮）
        self._type_income = QRadioButton("💰 收入")
        self._type_expense = QRadioButton("💸 支出")
        self._type_expense.setChecked(True)
        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self._type_income, 0)
        self._type_group.addButton(self._type_expense, 1)

        type_widget = QWidget()
        type_layout = QHBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(12)
        type_layout.addWidget(self._type_income)
        type_layout.addWidget(self._type_expense)
        type_layout.addStretch()

        # 类型切换时更新分类列表
        self._type_group.buttonClicked.connect(self._on_type_changed)

        form.addRow("类型:", type_widget)

        # 金额
        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 99999999.99)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setValue(0.01)
        self._amount_spin.setPrefix("¥ ")
        form.addRow("金额:", self._amount_spin)

        # 分类
        self._category_combo = QComboBox()
        self._category_combo.setMaxVisibleItems(10)
        form.addRow("分类:", self._category_combo)

        # 属性
        self._attr_combo = QComboBox()
        self._attr_combo.setMaxVisibleItems(8)
        for key, label in ATTRIBUTES.items():
            self._attr_combo.addItem(label, key)
        self._attr_combo.setCurrentIndex(2)  # 默认"刚需"
        form.addRow("属性:", self._attr_combo)

        # 账户
        self._account_combo = QComboBox()
        self._account_combo.setMaxVisibleItems(8)
        self._account_combo.setMaxVisibleItems(8)
        form.addRow("账户:", self._account_combo)

        # 备注
        self._note_edit = QLineEdit()
        self._note_edit.setPlaceholderText="可选备注..."
        form.addRow("备注:", self._note_edit)

        layout.addLayout(form)
        layout.addSpacing(8)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("btnSecondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ---- 数据加载 ----

    def _load_categories(self):
        """加载分类列表。"""
        cats = get_all_categories()
        self._all_categories = cats
        self._refresh_category_combo()

    def _refresh_category_combo(self):
        """根据当前选中的类型刷新分类下拉。"""
        self._category_combo.clear()
        is_income = self._type_income.isChecked()
        key = "income" if is_income else "expense"
        for name in self._all_categories.get(key, []):
            self._category_combo.addItem(name)

    def _load_accounts(self):
        """加载账户列表。"""
        accounts = get_all_accounts()
        for acc in accounts:
            self._account_combo.addItem(acc)

    # ---- 编辑回填 ----

    def _populate(self, txn: Transaction):
        """回填编辑数据。"""
        self._date_edit.setDate(QDate.fromString(txn.date, "yyyy-MM-dd"))

        if txn.type == "income":
            self._type_income.setChecked(True)
        else:
            self._type_expense.setChecked(True)
        self._refresh_category_combo()

        self._amount_spin.setValue(txn.amount)

        idx = self._category_combo.findText(txn.category)
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)

        idx = self._attr_combo.findData(txn.attribute)
        if idx >= 0:
            self._attr_combo.setCurrentIndex(idx)

        idx = self._account_combo.findText(txn.account)
        if idx >= 0:
            self._account_combo.setCurrentIndex(idx)

        self._note_edit.setText(txn.note)

    # ---- 事件 ----

    def _on_type_changed(self):
        """类型切换时更新分类下拉。"""
        self._refresh_category_combo()

    def _on_save(self):
        """保存交易。"""
        # 验证
        if self._amount_spin.value() <= 0:
            QMessageBox.warning(self, "输入错误", "金额必须大于 0")
            return

        category = self._category_combo.currentText().strip()
        if not category:
            QMessageBox.warning(self, "输入错误", "请选择或输入分类")
            return

        account = self._account_combo.currentText().strip()
        if not account:
            QMessageBox.warning(self, "输入错误", "请选择或输入账户")
            return

        txn_type = "income" if self._type_income.isChecked() else "expense"

        txn = Transaction(
            date=self._date_edit.date().toString("yyyy-MM-dd"),
            type=txn_type,
            amount=self._amount_spin.value(),
            category=category,
            attribute=self._attr_combo.currentData(),
            note=self._note_edit.text().strip(),
            account=account,
        )

        # 如果是编辑模式，保留原 ID
        if self._txn and self._txn.id is not None:
            txn.id = self._txn.id

        try:
            if txn.id is not None:
                TransactionService.update(txn)
            else:
                TransactionService.create(txn)
            self._result_txn = txn
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"数据库错误: {e}")
