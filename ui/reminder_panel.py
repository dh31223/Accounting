"""账单提醒管理面板。

- 提醒列表（名称/金额/到期日/周期/备注）
- 到期标记（即将到期黄色 / 已过期红色）
- 添加/编辑/删除提醒
"""

from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QDateEdit, QComboBox, QMessageBox, QHeaderView,
    QAbstractItemView, QMenu,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor, QColor

from core.reminder import ReminderService
from core.models import BillReminder

COLOR_CARD = "#16213e"
COLOR_EXPENSE = "#f87171"
COLOR_WARN = "#fbbf24"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_SECONDARY = "#94a3b8"

REPEAT_LABELS = {
    "none": "不重复",
    "monthly": "每月",
    "yearly": "每年",
}


class ReminderPanel(QWidget):
    """账单提醒管理面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("🔔 账单提醒")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("＋ 添加提醒")
        add_btn.clicked.connect(self._on_add)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # 到期汇总卡片
        self._due_card = QWidget()
        self._due_card.setObjectName("card")
        self._due_card.setVisible(False)
        due_layout = QHBoxLayout(self._due_card)
        due_layout.setContentsMargins(16, 10, 16, 10)
        self._due_label = QLabel("")
        self._due_label.setStyleSheet("background:transparent; font-size:14px;")
        due_layout.addWidget(self._due_label)
        due_layout.addStretch()
        layout.addWidget(self._due_card)

        # 提醒列表
        self._tree = QTreeWidget()
        self._tree.setColumnCount(5)
        self._tree.setHeaderLabels(["名称", "金额", "到期日", "周期", "备注"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_edit)

        header_view = self._tree.header()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setStretchLastSection(True)

        layout.addWidget(self._tree, stretch=1)

    def refresh(self):
        """刷新提醒列表。"""
        self._tree.clear()
        reminders = ReminderService.get_all()
        today = date.today()
        due_soon_list = []
        overdue_list = []

        for r in reminders:
            item = QTreeWidgetItem(self._tree)
            item.setText(0, r.name)
            amount_text = f"¥{r.amount:,.2f}" if r.amount else "—"
            item.setText(1, amount_text)
            item.setText(2, r.due_date)
            item.setText(3, REPEAT_LABELS.get(r.repeat_cycle, r.repeat_cycle))
            item.setText(4, r.note or "")
            item.setData(0, Qt.ItemDataRole.UserRole, r.id)

            # 到期标记
            due_d = date.fromisoformat(r.due_date)
            if due_d < today:
                # 已过期
                item.setForeground(2, QColor(COLOR_EXPENSE))
                item.setText(2, f"⚠ 已过期 {r.due_date}")
                overdue_list.append(r.name)
            elif due_d <= today + timedelta(days=7):
                # 7 天内到期
                item.setForeground(2, QColor(COLOR_WARN))
                item.setText(2, f"⏰ {r.due_date}")
                due_soon_list.append(r.name)

        # 到期汇总
        parts = []
        if overdue_list:
            parts.append(f"<span style='color:{COLOR_EXPENSE}'>⚠ 已过期: {', '.join(overdue_list)}</span>")
        if due_soon_list:
            parts.append(f"<span style='color:{COLOR_WARN}'>⏰ 即将到期: {', '.join(due_soon_list)}</span>")

        if parts:
            self._due_label.setText("  |  ".join(parts))
            self._due_card.setVisible(True)
        else:
            self._due_card.setVisible(False)

    # ---- CRUD ----

    def _on_add(self):
        dlg = ReminderDialog(self)
        if dlg.exec() == ReminderDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self, item: QTreeWidgetItem, col: int):
        rid = item.data(0, Qt.ItemDataRole.UserRole)
        if rid is None:
            return
        reminders = ReminderService.get_all()
        target = next((r for r in reminders if r.id == rid), None)
        if not target:
            return
        dlg = ReminderDialog(self, target)
        if dlg.exec() == ReminderDialog.DialogCode.Accepted:
            self.refresh()

    def _on_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        rid = item.data(0, Qt.ItemDataRole.UserRole)
        if rid is None:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("✏️ 编辑")
        delete_action = menu.addAction("🗑 删除")
        action = menu.exec(QCursor.pos())

        if action == edit_action:
            self._on_edit(item, 0)
        elif action == delete_action:
            self._delete(rid)

    def _delete(self, rid: int):
        reminders = ReminderService.get_all()
        target = next((r for r in reminders if r.id == rid), None)
        if not target:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除提醒「{target.name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ReminderService.delete(rid)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")


class ReminderDialog(QDialog):
    """添加/编辑提醒对话框。"""

    def __init__(self, parent, reminder: BillReminder = None):
        super().__init__(parent)
        self._reminder = reminder
        self._setup_ui()
        if reminder:
            self._populate(reminder)

    def _setup_ui(self):
        title = "编辑提醒" if self._reminder else "添加提醒"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 24)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:16px; font-weight:bold; color:#e2e8f0;")
        layout.addWidget(title_label)

        form = QFormLayout()
        form.setSpacing(12)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("账单名称，如「房租」")
        form.addRow("名称:", self._name_edit)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0, 99999999)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("¥ ")
        form.addRow("金额:", self._amount_spin)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(QDate.currentDate())
        form.addRow("到期日:", self._date_edit)

        self._repeat_combo = QComboBox()
        self._repeat_combo.setMaxVisibleItems(4)
        for key, label in REPEAT_LABELS.items():
            self._repeat_combo.addItem(label, key)
        form.addRow("重复:", self._repeat_combo)

        self._note_edit = QLineEdit()
        self._note_edit.setPlaceholderText("可选备注...")
        form.addRow("备注:", self._note_edit)

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

    def _populate(self, r: BillReminder):
        self._name_edit.setText(r.name)
        if r.amount is not None:
            self._amount_spin.setValue(r.amount)
        self._date_edit.setDate(QDate.fromString(r.due_date, "yyyy-MM-dd"))
        idx = self._repeat_combo.findData(r.repeat_cycle)
        if idx >= 0:
            self._repeat_combo.setCurrentIndex(idx)
        self._note_edit.setText(r.note or "")

    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "输入错误", "请输入账单名称")
            return

        reminder = BillReminder(
            name=name,
            amount=self._amount_spin.value() if self._amount_spin.value() > 0 else None,
            due_date=self._date_edit.date().toString("yyyy-MM-dd"),
            repeat_cycle=self._repeat_combo.currentData(),
            note=self._note_edit.text().strip(),
        )

        try:
            if self._reminder and self._reminder.id is not None:
                reminder.id = self._reminder.id
                ReminderService.update(reminder)
            else:
                ReminderService.create(reminder)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
