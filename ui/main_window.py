"""主窗口框架。

侧边导航 + QStackedWidget 内容区切换。
阶段 4 实现：交易记录（完整）、其他页面（占位）。
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QStatusBar,
    QButtonGroup, QApplication, QMessageBox,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from ui.theme import get_stylesheet, COLOR_SIDEBAR, COLOR_ACCENT, COLOR_TEXT_SECONDARY
from ui.transaction_panel import TransactionPanel
from ui.dashboard import DashboardPage
from ui.budget_panel import BudgetPanel
from ui.reminder_panel import ReminderPanel


# 导航项定义
NAV_ITEMS = [
    ("transactions", "📂 交易记录"),
    ("dashboard", "📊 统计仪表盘"),
    ("budget", "💰 预算管理"),
    ("reminders", "🔔 账单提醒"),
    ("templates", "📋 交易模板"),
    ("settings", "⚙️ 设置"),
]


class MainWindow(QMainWindow):
    """Accounting 主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accounting — 个人记账")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # 居中显示
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

        self._setup_ui()
        self._apply_theme()

    # ---- UI 构建 ----

    def _setup_ui(self):
        """构建主窗口布局。"""
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- 侧边栏 ----
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # ---- 内容区 ----
        self._stack = QStackedWidget()
        self._stack.setObjectName("contentArea")

        # 创建各页面
        self._transaction_panel = TransactionPanel()
        self._dashboard_page = DashboardPage()
        self._budget_page = BudgetPanel()
        self._reminders_page = ReminderPanel()
        self._templates_page = self._placeholder_page("📋 交易模板", "将在阶段 7 实现")
        self._settings_page = self._placeholder_page("⚙️ 设置", "将在阶段 7 实现")

        self._stack.addWidget(self._transaction_panel)   # index 0
        self._stack.addWidget(self._dashboard_page)      # index 1
        self._stack.addWidget(self._budget_page)         # index 2
        self._stack.addWidget(self._reminders_page)      # index 3
        self._stack.addWidget(self._templates_page)      # index 4
        self._stack.addWidget(self._settings_page)       # index 5

        root_layout.addWidget(self._stack, stretch=1)

        # ---- 状态栏 ----
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            f"QStatusBar{{background-color:{COLOR_SIDEBAR};color:{COLOR_TEXT_SECONDARY};"
            f"border-top:1px solid #2d3a5c;padding:4px 12px;}}"
        )
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

        # 连接交易面板的状态消息
        self._transaction_panel.status_message.connect(self._status_bar.showMessage)

        # 默认选中交易记录页
        self._nav_buttons[0].setChecked(True)
        self._switch_page(0)

    def _build_sidebar(self) -> QWidget:
        """构建侧边导航栏。"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("💰 Accounting")
        logo.setObjectName("logo")
        layout.addWidget(logo)

        subtitle = QLabel("个人记账 · 智慧理财")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # 导航按钮组
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        for i, (key, label) in enumerate(NAV_ITEMS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            self._nav_group.addButton(btn, i)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 底部版本号
        version_label = QLabel("v1.0.0 · Phase 4")
        version_label.setObjectName("subtitle")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        layout.addSpacing(12)

        return sidebar

    def _placeholder_page(self, icon: str, desc: str) -> QWidget:
        """创建占位页面。"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel(icon[0] if icon else "📋")
        icon_label.setStyleSheet("font-size:64px; background:transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(icon)
        title_label.setStyleSheet("font-size:24px; color:#e2e8f0; font-weight:bold; background:transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(desc)
        desc_label.setStyleSheet("font-size:14px; color:#94a3b8; background:transparent;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        return page

    # ---- 页面切换 ----

    def _switch_page(self, index: int):
        """切换内容页。"""
        self._stack.setCurrentIndex(index)

    # ---- 主题 ----

    def _apply_theme(self):
        """应用深色主题。"""
        self.setStyleSheet(get_stylesheet())

    # ---- 键盘快捷键 ----

    def keyPressEvent(self, event):
        """全局快捷键。"""
        if event.key() == Qt.Key.Key_N and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+N: 添加交易（需在交易页）
            if self._stack.currentIndex() == 0:
                self._transaction_panel._on_add()
        super().keyPressEvent(event)
