"""深色主题 QSS 样式表。

设计系统：
- 背景: #1a1a2e (base), #0f0f23 (sidebar), #16213e (card)
- 强调: #818cf8 (indigo), #a78bfa (purple)
- 收入: #34d399 (green), 支出: #f87171 (red)
- 文字: #e2e8f0 (primary), #94a3b8 (secondary)
"""

# ============================================================
# 颜色常量
# ============================================================

COLOR_BG = "#1a1a2e"
COLOR_SIDEBAR = "#0f0f23"
COLOR_CARD = "#16213e"
COLOR_ACCENT = "#818cf8"
COLOR_ACCENT_HOVER = "#9b9ef8"
COLOR_PURPLE = "#a78bfa"
COLOR_INCOME = "#34d399"
COLOR_EXPENSE = "#f87171"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_BORDER = "#2d3a5c"
COLOR_HOVER = "#1e2d4a"
COLOR_SELECTED = "#1e3a5f"

# ============================================================
# QSS 样式表
# ============================================================


def get_stylesheet() -> str:
    """返回完整的 QSS 样式表。"""
    return f"""
/* ============================================================
   全局样式
   ============================================================ */

QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif;
    font-size: 14px;
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

/* ============================================================
   侧边栏
   ============================================================ */

#sidebar {{
    background-color: {COLOR_SIDEBAR};
    border-right: 1px solid {COLOR_BORDER};
    min-width: 200px;
    max-width: 200px;
}}

#sidebar QLabel#logo {{
    color: {COLOR_ACCENT};
    font-size: 20px;
    font-weight: bold;
    padding: 24px 20px 16px 20px;
}}

#sidebar QLabel#subtitle {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    padding: 0px 20px 20px 20px;
}}

#sidebar QPushButton {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 20px;
    margin: 2px 10px;
    font-size: 14px;
}}

#sidebar QPushButton:hover {{
    background-color: {COLOR_HOVER};
    color: {COLOR_TEXT};
}}

#sidebar QPushButton:checked {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    font-weight: bold;
}}

/* ============================================================
   内容区
   ============================================================ */

#contentArea {{
    background-color: {COLOR_BG};
    padding: 0px;
}}

#pageTitle {{
    font-size: 24px;
    font-weight: bold;
    color: {COLOR_TEXT};
    padding: 20px 24px 12px 24px;
}}

/* ============================================================
   卡片
   ============================================================ */

#card {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 16px;
}}

#cardTitle {{
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

#cardValue {{
    font-size: 28px;
    font-weight: bold;
    color: {COLOR_TEXT};
}}

/* ============================================================
   表格 / 树形控件
   ============================================================ */

QTreeWidget {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    color: {COLOR_TEXT};
    alternate-background-color: {COLOR_HOVER};
    outline: none;
    font-size: 13px;
}}

QTreeWidget::item {{
    padding: 6px 4px;
    border-bottom: 1px solid transparent;
}}

QTreeWidget::item:hover {{
    background-color: {COLOR_HOVER};
}}

QTreeWidget::item:selected {{
    background-color: {COLOR_SELECTED};
    color: {COLOR_TEXT};
}}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
}}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
}}

QHeaderView::section {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
    padding: 10px 8px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
}}

/* ============================================================
   输入控件
   ============================================================ */

QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: {COLOR_ACCENT};
}}

QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border-color: {COLOR_ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 6px;
}}

QComboBox::down-arrow {{
    border-image: none;
    width: 0;
    height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    selection-background-color: {COLOR_ACCENT};
    outline: none;
}}

QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

QDateEdit QCalendarWidget {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

QDateEdit QCalendarWidget QToolButton {{
    color: {COLOR_TEXT};
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}}

QDateEdit QCalendarWidget QToolButton:hover {{
    background-color: {COLOR_HOVER};
}}

QDateEdit QCalendarWidget QAbstractItemView:enabled {{
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT};
}}

/* ============================================================
   按钮
   ============================================================ */

QPushButton {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: #6d7be0;
}}

QPushButton#btnSecondary {{
    background-color: {COLOR_BORDER};
    color: {COLOR_TEXT};
}}

QPushButton#btnSecondary:hover {{
    background-color: #3d5a8c;
}}

QPushButton#btnDanger {{
    background-color: {COLOR_EXPENSE};
    color: #ffffff;
}}

QPushButton#btnDanger:hover {{
    background-color: #f98b8b;
}}

QPushButton#btnSuccess {{
    background-color: {COLOR_INCOME};
    color: #064e3b;
}}

QPushButton#btnSuccess:hover {{
    background-color: #5ce4ad;
}}

QPushButton#btnFab {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border-radius: 28px;
    min-width: 56px;
    max-width: 56px;
    min-height: 56px;
    max-height: 56px;
    font-size: 24px;
    padding: 0px;
}}

QPushButton#btnFab:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#btnSmall {{
    padding: 5px 12px;
    font-size: 12px;
    border-radius: 6px;
}}

/* ============================================================
   对话框
   ============================================================ */

QDialog {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
}}

QDialog QLabel {{
    background-color: transparent;
}}

/* ============================================================
   滚动条
   ============================================================ */

QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLOR_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_TEXT_SECONDARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLOR_BORDER};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLOR_TEXT_SECONDARY};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ============================================================
   消息框
   ============================================================ */

QMessageBox {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
}}

QMessageBox QLabel {{
    color: {COLOR_TEXT};
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 8px 16px;
}}

/* ============================================================
   进度条
   ============================================================ */

QProgressBar {{
    background-color: {COLOR_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    text-align: center;
    color: {COLOR_TEXT};
    font-size: 12px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 5px;
}}

QProgressBar#overspent::chunk {{
    background-color: {COLOR_EXPENSE};
}}

/* ============================================================
   标签页切换
   ============================================================ */

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background-color: {COLOR_CARD};
}}

QTabBar::tab {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border-bottom: 2px solid {COLOR_ACCENT};
}}

QTabBar::tab:hover {{
    background-color: {COLOR_HOVER};
}}

/* ============================================================
   提示工具
   ============================================================ */

QToolTip {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""
