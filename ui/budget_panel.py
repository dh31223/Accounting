"""预算管理面板。

- 月份选择 + 总预算设定 + 分项预算设定
- 进度条（正常绿色 → 超支红色）
- 超支分类红色高亮
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QPushButton, QLabel, QProgressBar,
    QDialog, QFormLayout, QDoubleSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from core.budget import BudgetService
from core.statistics import StatisticsService
from db.schema import get_all_categories

# 颜色
COLOR_CARD = "#16213e"
COLOR_BG = "#1a1a2e"
COLOR_ACCENT = "#818cf8"
COLOR_INCOME = "#34d399"
COLOR_EXPENSE = "#f87171"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_WARN = "#fbbf24"


class BudgetPanel(QWidget):
    """预算管理面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._budget_widgets = {}  # category → progress bar widget
        self._setup_ui()
        self.refresh()

    # ---- UI ----

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("💰 预算管理")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        # 月份选择
        self._add_label(header, "月份")
        self._month_combo = QComboBox()
        self._month_combo.setMinimumWidth(120)
        self._month_combo.setMaxVisibleItems(10)
        self._populate_months()
        self._month_combo.currentTextChanged.connect(self.refresh)
        header.addWidget(self._month_combo)

        layout.addLayout(header)

        # 总预算卡片
        total_card = QWidget()
        total_card.setObjectName("card")
        total_layout = QVBoxLayout(total_card)
        total_layout.setContentsMargins(20, 14, 20, 14)
        total_layout.setSpacing(8)

        total_header = QHBoxLayout()
        total_title = QLabel("总预算")
        total_title.setStyleSheet("font-size:15px; font-weight:bold; color:#e2e8f0; background:transparent;")
        total_header.addWidget(total_title)
        total_header.addStretch()

        self._total_budget_label = QLabel("未设定")
        self._total_budget_label.setStyleSheet("color:#94a3b8; background:transparent; font-size:13px;")
        total_header.addWidget(self._total_budget_label)

        set_total_btn = QPushButton("设定")
        set_total_btn.setObjectName("btnSmall")
        set_total_btn.clicked.connect(lambda: self._on_set_budget(None))
        total_header.addWidget(set_total_btn)

        total_layout.addLayout(total_header)

        self._total_progress = QProgressBar()
        self._total_progress.setMinimum(0)
        self._total_progress.setMaximum(100)
        self._total_progress.setValue(0)
        self._total_progress.setFormat("¥0 / ¥0")
        self._total_progress.setTextVisible(True)
        total_layout.addWidget(self._total_progress)

        layout.addWidget(total_card)

        # 超支提示
        self._overspend_label = QLabel("")
        self._overspend_label.setStyleSheet(
            "color:#f87171; font-size:13px; font-weight:bold; background:transparent; padding:4px 8px;"
        )
        self._overspend_label.setVisible(False)
        layout.addWidget(self._overspend_label)

        # 分项预算网格
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(12)
        layout.addWidget(self._grid_widget)

        layout.addStretch()

    def _add_label(self, layout, text: str):
        label = QLabel(f"{text}:")
        label.setStyleSheet("background:transparent; color:#94a3b8; font-size:13px; border:none;")
        layout.addWidget(label)

    def _populate_months(self):
        """填入最近 12 个月供选择。"""
        today = date.today()
        for i in range(11, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            key = f"{y}-{m:02d}"
            self._month_combo.addItem(key, key)
        self._month_combo.setCurrentIndex(11)  # 当月

    # ---- 数据刷新 ----

    def refresh(self):
        """刷新预算数据。"""
        period = self._month_combo.currentData()
        if not period:
            return

        # 清空分项
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取预算
        budgets = BudgetService.get_budgets(period)
        budget_map = {b.category: b.amount for b in budgets}

        # 获取实际支出
        cats = get_all_categories()
        expense_cats = cats.get("expense", [])
        summary = StatisticsService.summary_by_period(f"{period}-01", self._end_of_month(period))
        total_spent = summary["total_expense"]
        cat_breakdown = {
            d["category"]: d["amount"]
            for d in StatisticsService.category_breakdown(f"{period}-01", self._end_of_month(period), "expense")
        }

        # 总预算
        total_budget = budget_map.get(None, 0.0)
        if total_budget > 0:
            self._total_budget_label.setText(f"¥{total_budget:,.0f}")
            pct = min(total_spent / total_budget * 100, 100)
            self._total_progress.setValue(int(pct))
            self._total_progress.setFormat(f"¥{total_spent:,.0f} / ¥{total_budget:,.0f}")
            if total_spent > total_budget:
                self._total_progress.setObjectName("overspent")
                self._total_progress.style().unpolish(self._total_progress)
                self._total_progress.style().polish(self._total_progress)
            else:
                self._total_progress.setObjectName("")
                self._total_progress.style().unpolish(self._total_progress)
                self._total_progress.style().polish(self._total_progress)
        else:
            self._total_budget_label.setText("未设定")
            self._total_progress.setValue(0)
            self._total_progress.setFormat("¥0 / ¥0")

        # 分项预算（2列网格）
        row = 0
        col = 0
        for cat in expense_cats:
            cat_budget = budget_map.get(cat, 0.0)
            spent = cat_breakdown.get(cat, 0.0)
            card = self._make_category_card(cat, cat_budget, spent)
            self._grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # 超支检测
        overspent = BudgetService.check_overspend(period)
        if overspent:
            lines = []
            for o in overspent:
                lines.append(f"⚠ {o['category']}: 预算 ¥{o['budget']:,.0f} / 实际 ¥{o['spent']:,.0f} ({o['pct']}%)")
            self._overspend_label.setText("  |  ".join(lines))
            self._overspend_label.setVisible(True)
        else:
            self._overspend_label.setVisible(False)

    def _make_category_card(self, cat_name: str, budget: float, spent: float) -> QWidget:
        """创建单分类预算卡片。"""
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # 标题行
        header = QHBoxLayout()
        cat_label = QLabel(cat_name)
        cat_label.setStyleSheet("font-size:14px; font-weight:bold; color:#e2e8f0; background:transparent;")
        header.addWidget(cat_label)
        header.addStretch()

        if budget > 0:
            budget_label = QLabel(f"预算 ¥{budget:,.0f}")
            budget_label.setStyleSheet("color:#94a3b8; font-size:12px; background:transparent;")
            header.addWidget(budget_label)

        set_btn = QPushButton("设定")
        set_btn.setObjectName("btnSmall")
        set_btn.clicked.connect(lambda checked, c=cat_name: self._on_set_budget(c))
        header.addWidget(set_btn)

        layout.addLayout(header)

        # 进度条
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        if budget > 0:
            pct = min(spent / budget * 100, 100)
            progress.setValue(int(pct))
            progress.setFormat(f"¥{spent:,.0f} / ¥{budget:,.0f}")
            if spent > budget:
                progress.setObjectName("overspent")
        else:
            progress.setValue(0)
            progress.setFormat(f"已花 ¥{spent:,.0f}")

        progress.setTextVisible(True)
        layout.addWidget(progress)

        return card

    def _end_of_month(self, period: str) -> str:
        """返回月份的最后一天。"""
        import calendar
        y, m = period.split("-")
        last = calendar.monthrange(int(y), int(m))[1]
        return f"{period}-{last:02d}"

    # ---- 设定预算弹窗 ----

    def _on_set_budget(self, category: str | None):
        """打开设定预算对话框。"""
        period = self._month_combo.currentData()
        dlg = BudgetDialog(self, category, period)
        if dlg.exec() == BudgetDialog.DialogCode.Accepted:
            self.refresh()


class BudgetDialog(QDialog):
    """设定预算对话框。"""

    def __init__(self, parent, category: str | None, period: str):
        super().__init__(parent)
        self._category = category
        self._period = period
        self._setup_ui()

    def _setup_ui(self):
        title = f"设定总预算 — {self._period}" if self._category is None else f"设定 {self._category} 预算 — {self._period}"
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 24)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:16px; font-weight:bold; color:#e2e8f0;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        form = QFormLayout()
        form.setSpacing(12)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0, 99999999)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("¥ ")
        self._amount_spin.setValue(0)
        form.addRow("预算金额:", self._amount_spin)

        layout.addLayout(form)

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

    def _on_save(self):
        amount = self._amount_spin.value()
        try:
            BudgetService.set_budget(self._category, amount, self._period)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
