"""统计仪表盘页面。

- 顶部：统计卡片（收入/支出/结余）
- 自定义日期范围选择
- 消费趋势折线图（日/周/月切换）
- 支出分类饼图 + 属性分布饼图
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QDateEdit, QComboBox, QPushButton, QLabel, QSizePolicy,
    QButtonGroup, QRadioButton,
)
from PyQt6.QtCore import Qt, QDate

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.statistics import StatisticsService
from db.schema import get_all_categories

# ---- matplotlib 中文字体设置 ----
import matplotlib.font_manager as fm
_CN_FONT = None
for name in ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
             "Microsoft YaHei", "SimHei", "AR PL UMing CN", "sans-serif"]:
    for f in fm.fontManager.ttflist:
        if name.lower() in f.name.lower():
            _CN_FONT = f.name
            break
    if _CN_FONT:
        break

if _CN_FONT:
    matplotlib.rcParams["font.family"] = _CN_FONT
matplotlib.rcParams["axes.unicode_minus"] = False

# 深色主题色板
PLOT_BG = "#16213e"
PLOT_TEXT = "#94a3b8"
PLOT_INCOME = "#34d399"
PLOT_EXPENSE = "#f87171"
PLOT_ACCENT = "#818cf8"
PLOT_PURPLE = "#a78bfa"
PIE_COLORS = ["#818cf8", "#34d399", "#f87171", "#a78bfa", "#fbbf24",
              "#f472b6", "#38bdf8", "#fb923c"]


class DashboardPage(QWidget):
    """统计仪表盘页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    # ---- UI 构建 ----

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📊 统计仪表盘")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ---- 日期范围 ----
        date_card = QWidget()
        date_card.setObjectName("card")
        date_row = QHBoxLayout(date_card)
        date_row.setContentsMargins(16, 12, 16, 12)
        date_row.setSpacing(10)

        self._add_label(date_row, "从")
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setMinimumWidth(130)
        date_row.addWidget(self._date_from)

        self._add_label(date_row, "至")
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setMinimumWidth(130)
        date_row.addWidget(self._date_to)

        refresh_btn = QPushButton("📊 统计")
        refresh_btn.setObjectName("btnSmall")
        refresh_btn.clicked.connect(self.refresh)
        date_row.addWidget(refresh_btn)
        date_row.addStretch()

        layout.addWidget(date_card)

        # ---- 统计卡片 ----
        cards_widget = QWidget()
        cards_grid = QHBoxLayout(cards_widget)
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setSpacing(16)

        self._income_card = self._make_stat_card("💰 本月收入", "¥ 0.00", PLOT_INCOME)
        self._expense_card = self._make_stat_card("💸 本月支出", "¥ 0.00", PLOT_EXPENSE)
        self._balance_card = self._make_stat_card("📊 结余", "¥ 0.00", PLOT_ACCENT)

        cards_grid.addWidget(self._income_card, stretch=1)
        cards_grid.addWidget(self._expense_card, stretch=1)
        cards_grid.addWidget(self._balance_card, stretch=1)

        layout.addWidget(cards_widget)

        # ---- 趋势图 + 切换按钮 ----
        trend_card = QWidget()
        trend_card.setObjectName("card")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(16, 12, 16, 12)
        trend_layout.setSpacing(8)

        # 标题行 + 切换按钮
        trend_header = QHBoxLayout()
        trend_title = QLabel("📈 消费趋势")
        trend_title.setStyleSheet("font-size:15px; font-weight:bold; color:#e2e8f0; background:transparent;")
        trend_header.addWidget(trend_title)
        trend_header.addStretch()

        self._trend_group = QButtonGroup(self)
        self._trend_group.setExclusive(True)
        for i, (key, label) in enumerate([
            ("daily", "日"), ("weekly", "周"), ("monthly", "月")
        ]):
            btn = QRadioButton(label)
            btn.setStyleSheet(
                "QRadioButton { color: #94a3b8; background: transparent; padding: 4px 12px; "
                "border: 1px solid #2d3a5c; border-radius: 4px; }"
                "QRadioButton:checked { color: #ffffff; background: #818cf8; border-color: #818cf8; }"
            )
            btn.clicked.connect(lambda checked, g=key: self._draw_trend(g))
            self._trend_group.addButton(btn)
            trend_header.addWidget(btn)
            if i == 1:
                btn.setChecked(True)  # 默认"周"

        trend_layout.addLayout(trend_header)

        self._trend_canvas = FigureCanvas(Figure(figsize=(6, 2.8), dpi=100, facecolor=PLOT_BG))
        self._trend_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        trend_layout.addWidget(self._trend_canvas)

        layout.addWidget(trend_card, stretch=1)

        # ---- 饼图行 ----
        pies_widget = QWidget()
        pies_layout = QHBoxLayout(pies_widget)
        pies_layout.setContentsMargins(0, 0, 0, 0)
        pies_layout.setSpacing(16)

        # 支出分类饼图
        cat_card = QWidget()
        cat_card.setObjectName("card")
        cat_layout = QVBoxLayout(cat_card)
        cat_layout.setContentsMargins(12, 10, 12, 10)
        cat_title = QLabel("支出分类占比")
        cat_title.setStyleSheet("font-size:14px; font-weight:bold; color:#e2e8f0; background:transparent;")
        cat_layout.addWidget(cat_title)
        self._category_pie = FigureCanvas(Figure(figsize=(3.2, 2.6), dpi=100, facecolor=PLOT_BG))
        cat_layout.addWidget(self._category_pie)
        pies_layout.addWidget(cat_card, stretch=1)

        # 属性分布饼图
        attr_card = QWidget()
        attr_card.setObjectName("card")
        attr_layout = QVBoxLayout(attr_card)
        attr_layout.setContentsMargins(12, 10, 12, 10)
        attr_title = QLabel("属性分布")
        attr_title.setStyleSheet("font-size:14px; font-weight:bold; color:#e2e8f0; background:transparent;")
        attr_layout.addWidget(attr_title)
        self._attr_pie = FigureCanvas(Figure(figsize=(3.2, 2.6), dpi=100, facecolor=PLOT_BG))
        attr_layout.addWidget(self._attr_pie)
        pies_layout.addWidget(attr_card, stretch=1)

        layout.addWidget(pies_widget, stretch=1)

    # ---- 辅助方法 ----

    def _add_label(self, layout, text: str):
        label = QLabel(f"{text}:")
        label.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 13px; border: none;"
        )
        layout.addWidget(label)

    def _make_stat_card(self, title_text: str, value_text: str, accent_color: str) -> QWidget:
        """创建统计数字卡片。"""
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size:13px; color:#94a3b8; font-weight:bold; background:transparent;")
        layout.addWidget(title_label)

        value_label = QLabel(value_text)
        value_label.setStyleSheet(
            f"font-size:28px; font-weight:bold; color:{accent_color}; background:transparent;"
        )
        value_label.setObjectName("statValue")
        layout.addWidget(value_label)

        # 把 label 引用存到 card 上方便更新
        card._value_label = value_label
        card._accent_color = accent_color

        return card

    # ---- 数据刷新 ----

    def refresh(self):
        """刷新全部数据。"""
        start = self._date_from.date().toString("yyyy-MM-dd")
        end = self._date_to.date().toString("yyyy-MM-dd")

        # 1. 汇总
        summary = StatisticsService.summary_by_period(start, end)
        self._update_card(self._income_card, f"¥ {summary['total_income']:,.2f}")
        self._update_card(self._expense_card, f"¥ {summary['total_expense']:,.2f}")
        self._update_card(self._balance_card, f"¥ {summary['balance']:,.2f}")

        # 2. 趋势图
        current_granularity = "weekly"  # 默认
        checked = self._trend_group.checkedButton()
        if checked:
            mapping = {"日": "daily", "周": "weekly", "月": "monthly"}
            current_granularity = mapping.get(checked.text(), "weekly")
        self._draw_trend(current_granularity)

        # 3. 饼图
        self._draw_category_pie(start, end)
        self._draw_attr_pie(start, end)

    def _update_card(self, card: QWidget, text: str):
        """更新统计卡片数值。"""
        lbl = getattr(card, "_value_label", None)
        if lbl:
            lbl.setText(text)

    # ---- 趋势折线图 ----

    def _draw_trend(self, granularity: str = "weekly"):
        """绘制消费趋势折线图。"""
        start = self._date_from.date().toString("yyyy-MM-dd")
        end = self._date_to.date().toString("yyyy-MM-dd")

        data = StatisticsService.spending_trend(start, end, granularity)
        self._trend_canvas.figure.clear()
        ax = self._trend_canvas.figure.add_subplot(111)
        ax.set_facecolor(PLOT_BG)

        if not data:
            ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                    color=PLOT_TEXT, fontsize=14, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            # 数据点多时降采样，避免卡死
            n = len(data)
            step = max(1, n // 30)  # 最多显示 ~30 个标签
            use_markers = n <= 60   # 超过 60 个点不画 marker

            labels = [d["label"] for d in data]
            short_labels = self._shorten_labels(labels, granularity)
            expenses = [d["expense"] for d in data]
            incomes = [d["income"] for d in data]
            x = range(n)

            mk = "o" if use_markers else ""
            ms = 5 if use_markers else 0

            ax.plot(x, expenses, color=PLOT_EXPENSE, linewidth=1.5, marker=mk,
                    markersize=ms, label="支出")
            ax.plot(x, incomes, color=PLOT_INCOME, linewidth=1.5, marker=mk,
                    markersize=ms, label="收入")

            ax.fill_between(x, expenses, alpha=0.08, color=PLOT_EXPENSE)
            ax.fill_between(x, incomes, alpha=0.08, color=PLOT_INCOME)

            # 每隔 step 个点显示一个标签
            tick_positions = list(range(0, n, step))
            tick_labels = [short_labels[i] for i in tick_positions]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, fontsize=9, color=PLOT_TEXT)
            ax.tick_params(axis="y", colors=PLOT_TEXT, labelsize=9)
            ax.legend(loc="upper right", facecolor=PLOT_BG, edgecolor="none",
                     labelcolor=PLOT_TEXT, fontsize=9)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#2d3a5c")
        ax.spines["bottom"].set_color("#2d3a5c")
        ax.tick_params(colors=PLOT_TEXT, labelsize=9)
        ax.grid(axis="y", color="#2d3a5c", linewidth=0.5, alpha=0.5)

        self._trend_canvas.figure.tight_layout(pad=1.5)
        self._trend_canvas.draw()

    def _shorten_labels(self, labels: list[str], granularity: str) -> list[str]:
        """缩短标签以避免拥挤。"""
        if granularity == "daily":
            # "2026-06-27" → "6/27"
            return [l[5:].replace("-", "/") for l in labels]
        elif granularity == "weekly":
            # "2026-06-22" → "6/22"
            return [l[5:].replace("-", "/") for l in labels]
        else:
            # "2026-06" → "6月"
            parts = [l.split("-") for l in labels]
            return [f"{int(p[1])}月" for p in parts]

    # ---- 饼图 ----

    def _draw_category_pie(self, start: str, end: str):
        """绘制支出分类占比饼图。"""
        data = StatisticsService.category_breakdown(start, end, "expense")
        self._category_pie.figure.clear()
        ax = self._category_pie.figure.add_subplot(111)
        ax.set_facecolor(PLOT_BG)

        if not data or all(d["amount"] == 0 for d in data):
            ax.text(0.5, 0.5, "暂无支出数据", ha="center", va="center",
                    color=PLOT_TEXT, fontsize=12, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            labels = [d["category"] for d in data]
            values = [d["amount"] for d in data]
            colors = PIE_COLORS[:len(data)]

            wedges, texts, autotexts = ax.pie(
                values, labels=None, autopct="%1.1f%%",
                colors=colors, startangle=90, pctdistance=0.75,
            )
            for t in autotexts:
                t.set_fontsize(8)
                t.set_color("#e2e8f0")

            ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5),
                     frameon=False, labelcolor=PLOT_TEXT, fontsize=9)

        self._category_pie.figure.tight_layout(pad=1.5)
        self._category_pie.draw()

    def _draw_attr_pie(self, start: str, end: str):
        """绘制属性分布饼图。"""
        data = StatisticsService.attribute_breakdown(start, end)
        self._attr_pie.figure.clear()
        ax = self._attr_pie.figure.add_subplot(111)
        ax.set_facecolor(PLOT_BG)

        if not data or all(d["amount"] == 0 for d in data):
            ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                    color=PLOT_TEXT, fontsize=12, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            labels = [d["label"] for d in data]
            values = [d["amount"] for d in data]
            colors = PIE_COLORS[:len(data)]

            wedges, texts, autotexts = ax.pie(
                values, labels=None, autopct="%1.1f%%",
                colors=colors, startangle=90, pctdistance=0.75,
            )
            for t in autotexts:
                t.set_fontsize(8)
                t.set_color("#e2e8f0")

            ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5),
                     frameon=False, labelcolor=PLOT_TEXT, fontsize=9)

        self._attr_pie.figure.tight_layout(pad=1.5)
        self._attr_pie.draw()
